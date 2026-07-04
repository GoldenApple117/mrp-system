"""邮件通知服务 — SMTP配置存数据库，部署不丢失"""
import smtplib
import os
import logging
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from datetime import datetime

logger = logging.getLogger(__name__)


def _get_db():
    """延迟导入避免循环依赖"""
    from app.core.database import SessionLocal
    from app.models.smtp_config import SmtpConfig
    db = SessionLocal()
    try:
        return db, SmtpConfig
    except:
        db.close()
        raise


def _get_or_create_config():
    """从数据库加载SMTP配置（合并环境变量凭据）"""
    from app.core.database import SessionLocal
    from app.models.smtp_config import SmtpConfig
    db = SessionLocal()
    try:
        cfg = db.query(SmtpConfig).first()
        if not cfg:
            cfg = SmtpConfig(id=1)
            db.add(cfg)
            db.commit()
            db.refresh(cfg)
        # 环境变量覆盖（仅在设置了非空值时）
        for attr, env in [("host","SMTP_HOST"),("port","SMTP_PORT"),("username","SMTP_USERNAME"),
                          ("password","SMTP_PASSWORD"),("from_addr","SMTP_FROM")]:
            val = os.getenv(env, "")
            if val:
                setattr(cfg, attr, int(val) if attr == "port" else val)
        return cfg
    finally:
        db.close()


def configure_smtp(host="", port=587, username="", password="", from_addr="", to_email=""):
    """配置SMTP参数（持久化到数据库）"""
    db, SmtpConfig = _get_db()
    try:
        cfg = db.query(SmtpConfig).first()
        if not cfg:
            cfg = SmtpConfig(id=1)
            db.add(cfg)
        if host: cfg.host = host
        if port: cfg.port = int(port)
        if username: cfg.username = username
        if password: cfg.password = password
        if from_addr: cfg.from_addr = from_addr
        if to_email: cfg.to_email = to_email
        db.commit()
        return get_smtp_config()
    finally:
        db.close()


def get_smtp_config():
    """获取当前SMTP配置（密码脱敏）"""
    cfg = _get_or_create_config()
    env_pwd = os.getenv("SMTP_PASSWORD", "")
    return {
        "host": cfg.host, "port": cfg.port,
        "username": cfg.username, "password": "***" if (cfg.password or env_pwd) else "",
        "from_addr": cfg.from_addr, "to_email": cfg.to_email,
    }


def get_full_config():
    """获取完整配置（含明文密码，仅内部使用）"""
    cfg = _get_or_create_config()
    env_pwd = os.getenv("SMTP_PASSWORD", "")
    return {
        "host": cfg.host, "port": cfg.port,
        "username": cfg.username, "password": env_pwd or cfg.password,
        "from_addr": cfg.from_addr, "to_email": cfg.to_email, "use_tls": True,
    }


def send_mrp_notification(result: dict):
    """发送MRP运算结果通知"""
    cf = get_full_config()
    to_email = cf["to_email"]
    if not to_email:
        logger.warning("[通知] 未配置接收邮箱")
        return False
    if not cf["host"] or not cf["username"]:
        logger.warning("[通知] SMTP未配置")
        return False

    subject = f"[MRP] 运算完成 — {result.get('exceptions', 0)}条例外"
    body = f"""<html><body style="font-family:Arial,sans-serif;color:#333;">
<h2>MRP 自动运算报告</h2>
<table style="border-collapse:collapse;width:100%;max-width:500px;">
<tr><td style="padding:8px;border-bottom:1px solid #eee;">时间</td>
<td style="padding:8px;">{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}</td></tr>
<tr><td style="padding:8px;border-bottom:1px solid #eee;">订单</td>
<td style="padding:8px;">{result.get('total_orders', 0)} 条</td></tr>
<tr><td style="padding:8px;border-bottom:1px solid #eee;">PO</td>
<td style="padding:8px;">{result.get('auto_po', 0)} 条</td></tr>
<tr><td style="padding:8px;">例外</td>
<td style="padding:8px;color:{'#e74c3c' if result.get('exceptions',0)>0 else '#27ae60'};font-weight:bold;">{result.get('exceptions', 0)} 条</td></tr>
</table><p style="margin-top:16px;color:#999;font-size:12px;">MRP II 系统自动发送</p></body></html>"""

    try:
        msg = MIMEMultipart("alternative")
        msg["Subject"] = subject
        msg["From"] = cf["from_addr"]
        msg["To"] = to_email
        msg.attach(MIMEText(body, "html", "utf-8"))
        server = smtplib.SMTP(cf["host"], int(cf["port"]), timeout=15)
        server.starttls()
        server.login(cf["username"], cf["password"])
        server.sendmail(cf["from_addr"], [t.strip() for t in to_email.split(",")], msg.as_string())
        server.quit()
        logger.info(f"[通知] 邮件已发送至 {to_email}")
        return True
    except Exception as e:
        logger.error(f"[通知] 发送失败: {e}")
        return False


def send_test_email(to_email: str):
    """发送测试邮件（返回详细错误信息用于诊断）"""
    cf = get_full_config()
    if not cf["host"]:
        return {"success": False, "message": "SMTP未配置，请先填写服务器信息"}

    subject = "[MRP] 邮件功能测试"
    body = f"""<html><body style="font-family:Arial,sans-serif;color:#333;">
<h2>MRP II 系统邮件测试</h2><p>这是一封自动测试邮件。如果您收到此邮件，说明邮件通知功能配置正确。</p>
<p>发送时间：{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}</p>
<p style="color:#999;font-size:12px;">MRP II 系统自动发送</p></body></html>"""

    try:
        msg = MIMEMultipart("alternative")
        msg["Subject"] = subject
        msg["From"] = cf["from_addr"]
        msg["To"] = to_email
        msg.attach(MIMEText(body, "html", "utf-8"))

        logger.info(f"[测试邮件] 连接 {cf['host']}:{cf['port']}, 用户={cf['username']}")
        server = smtplib.SMTP(cf["host"], int(cf["port"]), timeout=15)
        server.set_debuglevel(1)  # 输出SMTP会话详情
        server.ehlo()
        if cf.get("use_tls", True):
            server.starttls()
            server.ehlo()
        logger.info(f"[测试邮件] 正在登录...")
        server.login(cf["username"], cf["password"])
        logger.info(f"[测试邮件] 登录成功，正在发送至 {to_email}...")
        server.sendmail(cf["from_addr"], [to_email], msg.as_string())
        server.quit()
        logger.info(f"[测试邮件] 发送成功！")
        return {"success": True, "message": "测试邮件已发送，请查收"}
    except Exception as e:
        err = str(e)
        logger.error(f"[测试邮件] 发送失败: {err}")
        # 返回详细错误以便诊断
        return {"success": False, "message": f"SMTP错误: {err}"}
