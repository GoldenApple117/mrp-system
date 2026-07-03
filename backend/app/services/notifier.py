"""邮件通知服务 — MRP自动运算后发送邮件"""
import smtplib
import json
import os
import logging
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from datetime import datetime

logger = logging.getLogger(__name__)

# 配置文件路径（与backend同级）
_BASE = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
_CFG_FILE = os.path.join(_BASE, "smtp_config.json")

# SMTP 配置默认值
SMTP_CONFIG = {
    "host": "",
    "port": 587,
    "username": "",
    "password": "",
    "from_addr": "",
    "to_email": "",
    "use_tls": True,
}


def _load_config():
    """从JSON文件加载SMTP配置"""
    if os.path.exists(_CFG_FILE):
        try:
            with open(_CFG_FILE, "r", encoding="utf-8") as f:
                saved = json.load(f)
                SMTP_CONFIG.update(saved)
            logger.info("[邮件] 已加载SMTP配置")
        except Exception as e:
            logger.warning(f"[邮件] 加载配置失败: {e}")


def _save_config():
    """持久化SMTP配置到JSON文件（密码明文存储，生产环境建议用环境变量）"""
    try:
        with open(_CFG_FILE, "w", encoding="utf-8") as f:
            json.dump(SMTP_CONFIG, f, ensure_ascii=False, indent=2)
    except Exception as e:
        logger.error(f"[邮件] 保存配置失败: {e}")


# 模块加载时自动读取配置
_load_config()


def configure_smtp(host="", port=587, username="", password="", from_addr="", to_email=""):
    """配置SMTP参数（自动持久化）"""
    if host: SMTP_CONFIG["host"] = host
    if port: SMTP_CONFIG["port"] = int(port)
    if username: SMTP_CONFIG["username"] = username
    if password: SMTP_CONFIG["password"] = password
    if from_addr: SMTP_CONFIG["from_addr"] = from_addr
    if to_email: SMTP_CONFIG["to_email"] = to_email
    _save_config()
    return get_smtp_config()


def get_smtp_config():
    """获取当前SMTP配置（密码脱敏）"""
    cfg = dict(SMTP_CONFIG)
    if cfg.get("password"):
        cfg["password"] = "***"
    return cfg


def get_full_config():
    """获取完整配置（含明文密码，仅内部使用）"""
    return dict(SMTP_CONFIG)


def send_mrp_notification(result: dict):
    """发送MRP运算结果通知（自动使用配置中的to_email）"""
    to_email = SMTP_CONFIG.get("to_email", "")
    if not to_email:
        logger.warning("[通知] 未配置接收邮箱，跳过邮件发送")
        return False

    if not SMTP_CONFIG["host"] or not SMTP_CONFIG["username"]:
        logger.warning("[通知] SMTP未配置，跳过邮件发送")
        return False

    success = result.get("success", False)
    orders = result.get("total_orders", 0)
    exceptions = result.get("exceptions", 0)
    auto_po = result.get("auto_po", 0)

    subject = f"[MRP] {'✅' if success else '❌'} 运算完成 — {exceptions}条例外"
    
    body = f"""
    <html>
    <body style="font-family: Arial, sans-serif; color: #333;">
        <h2>MRP 自动运算报告</h2>
        <table style="border-collapse:collapse; width:100%; max-width:500px;">
            <tr><td style="padding:8px; border-bottom:1px solid #eee;">运算时间</td>
                <td style="padding:8px; border-bottom:1px solid #eee;">{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}</td></tr>
            <tr><td style="padding:8px; border-bottom:1px solid #eee;">计划订单</td>
                <td style="padding:8px; border-bottom:1px solid #eee;">{orders} 条</td></tr>
            <tr><td style="padding:8px; border-bottom:1px solid #eee;">自动生成PO</td>
                <td style="padding:8px; border-bottom:1px solid #eee;">{auto_po} 条</td></tr>
            <tr><td style="padding:8px; border-bottom:1px solid #eee;">例外数</td>
                <td style="padding:8px; color:{'#e74c3c' if exceptions > 0 else '#27ae60'}; font-weight:bold;">
                    {exceptions} 条</td></tr>
        </table>
        <p style="margin-top:16px; color:#999; font-size:12px;">
            此邮件由 MRP II 系统自动发送。
        </p>
    </body>
    </html>
    """

    try:
        msg = MIMEMultipart("alternative")
        msg["Subject"] = subject
        msg["From"] = SMTP_CONFIG["from_addr"]
        msg["To"] = to_email
        msg.attach(MIMEText(body, "html", "utf-8"))

        if SMTP_CONFIG["use_tls"]:
            server = smtplib.SMTP(SMTP_CONFIG["host"], int(SMTP_CONFIG["port"]), timeout=10)
            server.starttls()
        else:
            server = smtplib.SMTP_SSL(SMTP_CONFIG["host"], int(SMTP_CONFIG["port"]), timeout=10)

        server.login(SMTP_CONFIG["username"], SMTP_CONFIG["password"])
        server.sendmail(SMTP_CONFIG["from_addr"], to_email, msg.as_string())
        server.quit()
        logger.info(f"[通知] 邮件已发送至 {to_email}")
        return True
    except Exception as e:
        logger.error(f"[通知] 发送失败: {e}")
        return False


def send_test_email(to_email: str):
    """发送测试邮件"""
    if not SMTP_CONFIG["host"]:
        return {"success": False, "message": "SMTP未配置，请先填写服务器信息"}

    _cf = get_full_config()
    result = {
        "success": True, "total_orders": 0, "exceptions": 0,
        "auto_po": 0, "app_url": ""
    }

    # 临时用传入地址发一封测试邮件
    saved = SMTP_CONFIG["to_email"]
    SMTP_CONFIG["to_email"] = to_email or _cf.get("to_email", "")
    try:
        sent = send_mrp_notification(result)
        return {"success": sent, "message": "测试邮件已发送" if sent else "发送失败，请检查配置"}
    finally:
        SMTP_CONFIG["to_email"] = saved
