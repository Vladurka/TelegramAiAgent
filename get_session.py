import os
from dotenv import load_dotenv 
from telethon.sync import TelegramClient 
from telethon.sessions import StringSession 
from telethon.errors import SessionPasswordNeededError 

load_dotenv()

API_ID = int(os.getenv("API_ID"))
API_HASH = os.getenv("API_HASH")

if not API_ID or not API_HASH:
    raise Exception("❌ Make sure you have API_ID и API_HASH")

with TelegramClient(StringSession(), API_ID, API_HASH) as client:
    print("⚡ Connecting to Telegram...")

    if not client.is_user_authorized():
        phone = input("Enter phone number: ")
        client.send_code_request(phone)
        code = input("Enter code: ")

        try:
            client.sign_in(phone=phone, code=code)
        except SessionPasswordNeededError:
            password = input("Enter password: ")
            client.sign_in(password=password)
    else:
        print("✅ Authorized!")

    session_string = client.session.save()
    print("\n🎉 Session string created successfully:\n")
    print(session_string)
    print("\n💾 Add this to .env :\nSESSION_STRING=this string")
