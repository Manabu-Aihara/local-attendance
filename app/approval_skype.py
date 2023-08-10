import os

from skpy import Skype

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
