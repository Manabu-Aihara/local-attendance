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
def ask_approval(message):
    skype_obj = make_skype_object()
    for c in skype_obj.chats.recent():
        chat = skype_obj.chats[c]
        if hasattr(chat, 'topic') and chat.topic == os.getenv("SKYPE_TOPIC"):
            chat.sendMsg(message)
            break

def createMIMEText(mail_to: str, message: str):
    # MIMETextを作成
    # msg = MIMEText(message, "html")
    # msg = MIMEText(message)
    msg = MIMEText(message, "plain", 'utf-8')

    msg["Subject"] = "所属長からのコメント"
    msg["From"] = os.getenv("SKYPE_USER")
    msg["To"] = mail_to
    msg['Date'] = formatdate()

    return msg

def set_smtp(mail_text_func: MIMEText):
    host = os.getenv("OUTLOOK_HOST")
    port = 587

    server = SMTP(host, 587)
    # server.connect()
    server.starttls()
    server.login(os.getenv("SKYPE_USER"), os.getenv("SKYPE_PASSWORD"))

    server.send_message(mail_text_func)

    server.quit()

def send_mail(smtp_config_func: None, destination: str, message: str):
    mime_message = createMIMEText(destination, message)
    smtp_config_func(mime_message)
