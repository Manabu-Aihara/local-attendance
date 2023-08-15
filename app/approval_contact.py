import os

from skpy import Skype

from smtplib import SMTP

from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart

from email.utils import formatdate

from dotenv import load_dotenv
load_dotenv()

def make_skype_object():
    skype_obj = Skype(os.getenv("SKYPE_USER"), os.getenv("SKYPE_PASSWORD"))
    return skype_obj

# skypeの指定したグループにメッセージを送信(通知)する関数
# http://kakedashi-xx.com:25214/index.php/2021/04/08/post-2199/ を参照
def ask_approval(message):
    skype_obj = make_skype_object()
    for c in skype_obj.chats.recent():
        chat = skype_obj.chats[c]
        if hasattr(chat, 'topic') and chat.topic == os.getenv("SKYPE_TOPIC"):
            chat.sendMsg(message)
            break

# 以下https://zenn.dev/shimakaze_soft/articles/9601818a95309c を参考
def createMIMEText(mail_from: str, mail_to: str, message: str):
    # MIMETextを作成
    # msg = MIMEText(message, "html")
    # msg = MIMEText(message)
    msg = MIMEText(message, "plain", 'utf-8')

    msg["Subject"] = "所属長からのコメント"
    msg["From"] = mail_from
    msg["To"] = mail_to
    msg['Date'] = formatdate()

    return msg

def set_smtp(mail_text_func: MIMEText):
    host = os.getenv("OUTLOOK_HOST")
    # Literal[587]型なので注意
    port = 587

    server = SMTP(host, 587)
    # server.connect()
    server.starttls()
    server.login(os.getenv("SKYPE_USER"), os.getenv("SKYPE_PASSWORD"))

    server.send_message(mail_text_func)

    server.quit()

def send_mail(source: str, destination: str, message: str, smtp_config_func: None = set_smtp):
    mime_message = createMIMEText(source, destination, message)
    smtp_config_func(mime_message)
