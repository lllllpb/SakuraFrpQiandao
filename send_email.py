import smtplib
import os
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from email.mime.base import MIMEBase
from email import encoders
from datetime import datetime


def send_log_email(log_file='checkin.log'):
    """
    发送签到日志邮件
    
    Args:
        log_file: 日志文件路径
    """
    # 从环境变量读取配置
    smtp_server = os.getenv('SMTP_SERVER', 'smtp.gmail.com')
    smtp_port = int(os.getenv('SMTP_PORT', '587'))
    sender_email = os.getenv('EMAIL_USERNAME', '')
    sender_password = os.getenv('EMAIL_PASSWORD', '')
    receiver_email = os.getenv('RECEIVER_EMAIL', sender_email)
    
    # 检查配置
    if not sender_email or not sender_password:
        print("❌ 邮件配置未设置，跳过发送")
        return False
    
    try:
        # 读取日志内容
        log_content = ""
        if os.path.exists(log_file):
            with open(log_file, 'r', encoding='utf-8') as f:
                log_content = f.read()
        else:
            log_content = "日志文件不存在"
        
        # 判断签到是否成功（根据日志内容）
        is_success = "签到流程完成" in log_content or "验证码验证成功" in log_content
        status_emoji = "✅" if is_success else "❌"
        status_text = "成功" if is_success else "失败"
        
        # 创建邮件
        msg = MIMEMultipart()
        msg['From'] = sender_email
        msg['To'] = receiver_email
        msg['Subject'] = f"{status_emoji} SakuraFrp 签到{status_text} - {datetime.now().strftime('%Y-%m-%d')}"
        
        # 邮件正文
        body = f"""
SakuraFrp 自动签到报告

状态: {status_emoji} {status_text}
时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}

{'='*50}
日志内容:
{'='*50}

{log_content[-2000:] if len(log_content) > 2000 else log_content}

{'='*50}
此邮件由自动签到系统发送
        """
        
        msg.attach(MIMEText(body, 'plain', 'utf-8'))
        
        # 添加日志附件
        if os.path.exists(log_file):
            with open(log_file, 'rb') as f:
                part = MIMEBase('application', 'octet-stream')
                part.set_payload(f.read())
            encoders.encode_base64(part)
            part.add_header('Content-Disposition', f'attachment; filename= {os.path.basename(log_file)}')
            msg.attach(part)
        
        # 发送邮件
        with smtplib.SMTP(smtp_server, smtp_port) as server:
            server.starttls()
            server.login(sender_email, sender_password)
            server.send_message(msg)
        
        print(f"✅ 邮件发送成功: {receiver_email}")
        return True
        
    except Exception as e:
        print(f"❌ 邮件发送失败: {e}")
        return False


def send_bark(log_file='checkin.log'):
    """
    推送签到结果到 Bark（iPhone）

    环境变量：
      BARK_KEY    Bark 推送 key（必填，未设置则跳过）
      BARK_SERVER Bark 服务器，默认 https://api.day.app
      BARK_GROUP  推送分组名，默认 SakuraFrp

    Returns:
        bool: 是否推送成功
    """
    import json
    import urllib.request

    bark_key = os.getenv('BARK_KEY', '').strip()
    if not bark_key:
        print("❌ BARK_KEY 未设置，跳过 Bark 推送")
        return False

    server = os.getenv('BARK_SERVER', 'https://api.day.app').strip().rstrip('/')
    group = os.getenv('BARK_GROUP', 'SakuraFrp').strip()

    # 从日志判断结果
    log_content = ""
    if os.path.exists(log_file):
        with open(log_file, 'r', encoding='utf-8', errors='replace') as f:
            log_content = f.read()

    # workflow 在「重试后仍失败」时写入该标记，优先级高于日志正则
    fail_flag = 'checkin.failed'
    if os.path.exists(fail_flag):
        with open(fail_flag, 'r', encoding='utf-8', errors='replace') as f:
            flag = f.read().strip() or "首次运行与自动重试均失败"
        status_emoji, status_text, detail = "❌", "签到失败", flag
    elif "今日已签到" in log_content:
        status_emoji, status_text, detail = "🟡", "今日已签到", "今天之前已经签到过了"
    elif "签到流程完成" in log_content:
        status_emoji, status_text, detail = "✅", "签到成功", "已完成签到（含验证码）"
    elif "验证码验证成功" in log_content:
        status_emoji, status_text, detail = "✅", "签到成功", "验证码验证通过"
    else:
        status_emoji, status_text, detail = "❌", "签到失败", "未检测到签到完成标记，请查看日志"

    body = f"{detail}\n时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}"
    payload = {
        "title": f"{status_emoji} SakuraFrp 签到{status_text}",
        "body": body,
        "group": group,
        "level": "timeSensitive",
    }
    run_url = os.getenv('RUN_URL', '').strip()
    if run_url:
        payload["url"] = run_url
    payload = json.dumps(payload).encode('utf-8')

    req = urllib.request.Request(
        f"{server}/{bark_key}",
        data=payload,
        headers={"Content-Type": "application/json; charset=utf-8", "User-Agent": "curl/8.5.0"},
        method="POST",
    )
    try:
        with urllib.request.urlopen(req, timeout=15) as resp:
            result = json.loads(resp.read().decode('utf-8'))
        if result.get("code") == 200:
            print(f"✅ Bark 推送成功: {status_text}")
            return True
        print(f"❌ Bark 推送失败: {result}")
        return False
    except Exception as e:
        print(f"❌ Bark 推送异常: {e}")
        return False


def notify_all(log_file='checkin.log'):
    """统一通知入口：邮件 + Bark，任一失败不影响另一个。"""
    send_log_email(log_file)
    send_bark(log_file)


if __name__ == "__main__":
    notify_all()