"""邮件通知服务 — QQ SMTP 版本"""
import os
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from datetime import datetime
from app.core.database import SessionLocal
from app.models.smtp_config import SmtpConfig

logger = __import__("logging").getLogger(__name__)


def get_full_config():
    """读取邮件配置（数据库 + 环境变量覆盖）"""
    db = SessionLocal()
    try:
        cfg = db.query(SmtpConfig).first()
        if not cfg:
            cfg = SmtpConfig()
            db.add(cfg)
            db.commit()
            db.refresh(cfg)

        # 环境变量覆盖（仅当非空时）
        for attr, env in [
            ("host", "SMTP_HOST"),
            ("port", "SMTP_PORT"),
            ("username", "SMTP_USERNAME"),
            ("password", "SMTP_PASSWORD"),
            ("from_addr", "SMTP_FROM"),
        ]:
            val = os.getenv(env, "")
            if val:
                setattr(cfg, attr, int(val) if attr == "port" else val)
        return cfg
    finally:
        db.close()


def get_smtp_config():
    """获取邮件配置（密码脱敏），供 API 调用"""
    cfg = get_full_config()
    return {
        "host": cfg.host,
        "port": cfg.port,
        "username": cfg.username,
        "password": "***" if cfg.password else "",
        "from_addr": cfg.from_addr,
        "to_email": cfg.to_email,
        "use_tls": bool(cfg.use_tls),
    }


def configure_smtp(**kwargs):
    """保存邮件配置到数据库"""
    db = SessionLocal()
    try:
        cfg = db.query(SmtpConfig).first()
        if not cfg:
            cfg = SmtpConfig()
            db.add(cfg)
            db.flush()

        for key, val in kwargs.items():
            if hasattr(cfg, key) and val is not None:
                setattr(cfg, key, val)

        db.commit()
        return {
            "host": cfg.host,
            "port": cfg.port,
            "username": cfg.username,
            "from_addr": cfg.from_addr,
            "to_email": cfg.to_email,
            "password": "***" if cfg.password else "",
        }
    finally:
        db.close()


def send_mrp_notification(result: dict):
    """
    发送 MRP 结果邮件（后台定时任务调用）
    result: {"success": True, "total_orders": N, "exceptions": N, "auto_po": N}
    """
    cf = get_full_config()
    if not cf.host or not cf.password:
        logger.warning("[邮件] SMTP 未配置，跳过发送")
        return False

    to_list = [x.strip() for x in (cf.to_email or "").split(",") if x.strip()]
    if not to_list:
        logger.warning("[邮件] 收件人为空，跳过发送")
        return False

    subject = f"[MRP] 定时运算报告 {datetime.now().strftime('%Y-%m-%d')}"
    body = f"""<html><body style="font-family:Arial,sans-serif;color:#333;">
<h2>MRP 定时运算报告</h2>
<p>运算时间：{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}</p>
<ul>
  <li>计划订单总数：<b>{result.get('total_orders', 0)}</b></li>
  <li>例外报告数：<b>{result.get('exceptions', 0)}</b></li>
  <li>自动生成采购单：<b>{result.get('auto_po', 0)}</b></li>
</ul>
<p style="color:#999;font-size:12px;">MRP II 系统自动发送，请勿回复。</p>
</body></html>"""

    try:
        msg = MIMEMultipart("alternative")
        msg["Subject"] = subject
        msg["From"] = cf.from_addr or cf.username
        msg["To"] = ", ".join(to_list)
        msg.attach(MIMEText(body, "html", "utf-8"))

        server = smtplib.SMTP(cf.host, int(cf.port), timeout=15)
        if cf.use_tls:
            server.starttls()
        server.login(cf.username, cf.password)
        server.sendmail(cf.from_addr or cf.username, to_list, msg.as_string())
        server.quit()
        logger.info(f"[邮件] 发送成功 → {to_list}")
        return True
    except Exception as e:
        logger.error(f"[邮件] 发送失败: {e}")
        return False


def send_test_email(to_email: str):
    """发送测试邮件（返回详细错误信息用于诊断）"""
    cf = get_full_config()
    if not cf.host:
        return {"success": False, "message": "SMTP未配置，请先填写服务器信息"}

    subject = "[MRP] 邮件功能测试"
    body = f"""<html><body style="font-family:Arial,sans-serif;color:#333;">
<h2>MRP II 系统邮件测试</h2>
<p>这是一封自动测试邮件。如果您收到此邮件，说明邮件通知功能配置正确。</p>
<p>发送时间：{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}</p>
<p style="color:#999;font-size:12px;">MRP II 系统自动发送</p>
</body></html>"""

    try:
        msg = MIMEMultipart("alternative")
        msg["Subject"] = subject
        msg["From"] = cf.from_addr or cf.username
        msg["To"] = to_email
        msg.attach(MIMEText(body, "html", "utf-8"))

        logger.info(f"[测试邮件] 连接 {cf.host}:{cf.port}, 用户={cf.username}")
        server = smtplib.SMTP(cf.host, int(cf.port), timeout=15)
        if cf.use_tls:
            server.starttls()
        logger.info("[测试邮件] 正在登录...")
        server.login(cf.username, cf.password)
        logger.info("[测试邮件] 登录成功，正在发送...")
        server.sendmail(cf.from_addr or cf.username, [to_email], msg.as_string())
        server.quit()
        logger.info("[测试邮件] 发送成功！")
        return {"success": True, "message": "测试邮件已发送，请查收"}
    except Exception as e:
        err = str(e)
        logger.error(f"[测试邮件] 发送失败: {err}")
        return {"success": False, "message": f"SMTP错误: {err}"}
