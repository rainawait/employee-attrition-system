"""邮件发送模块 —— QQ 邮箱 SMTP (SSL) 发送报告附件"""
import os
import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from email.mime.base import MIMEBase
from email.header import Header
from email import encoders
from report.config import SMTP_CONFIG

CURRENT_DIR = os.path.dirname(os.path.abspath(__file__))
REPORT_DIR = os.path.abspath(os.path.join(CURRENT_DIR, '..', 'reports'))


def send_report_email(recipient, report_path=None):
    """
    发送报告到指定邮箱
    使用 QQ 邮箱 SMTP SSL (465 端口)，需要先在 config.py 中配置授权码
    """
    username = SMTP_CONFIG.get('username', '')
    password = SMTP_CONFIG.get('password', '')

    if not username or not password:
        raise RuntimeError(
            '邮箱未配置。请在 report/config.py 的 SMTP_CONFIG 中填写：\n'
            '  username: 你的 QQ 邮箱地址\n'
            '  password: QQ 邮箱 SMTP 16 位授权码（非 QQ 密码）\n'
            '获取授权码：QQ 邮箱 → 设置 → 账户 → POP3/IMAP/SMTP 服务 → 开启 SMTP → 获取授权码')

    if report_path is None:
        report_path = os.path.join(REPORT_DIR, 'analysis_report.png')
    if not os.path.exists(report_path):
        raise FileNotFoundError(f'报告文件不存在: {report_path}')

    msg = MIMEMultipart()
    msg['From'] = username
    msg['To'] = recipient
    msg['Subject'] = Header('员工离职综合分析报告', 'utf-8').encode()

    body = ('您好，\n\n'
            '附件为自动生成的员工离职综合分析报告，请查收。\n\n'
            '此邮件由系统自动发送，请勿回复。\n'
            '内部资料 — 仅限 HR 部门使用')
    msg.attach(MIMEText(body, 'plain', 'utf-8'))

    with open(report_path, 'rb') as f:
        part = MIMEBase('application', 'octet-stream')
        part.set_payload(f.read())
        encoders.encode_base64(part)
        part.add_header('Content-Disposition',
                        f'attachment; filename={os.path.basename(report_path)}')
        msg.attach(part)

    if SMTP_CONFIG.get('use_ssl'):
        server = smtplib.SMTP_SSL(SMTP_CONFIG['server'], SMTP_CONFIG['port'], timeout=30)
    else:
        server = smtplib.SMTP(SMTP_CONFIG['server'], SMTP_CONFIG['port'], timeout=30)
        server.starttls()

    server.login(username, password)
    server.sendmail(username, recipient, msg.as_string())
    server.quit()
