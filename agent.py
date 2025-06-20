import os
from dotenv import load_dotenv 
from telethon import TelegramClient, events
from telethon.sessions import StringSession 
from telethon.tl.types import Message
from telethon.errors import FloodWaitError
import openai
import random

load_dotenv()

API_ID = int(os.getenv("API_ID"))
API_HASH = os.getenv("API_HASH")
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
SESSION_STRING = os.getenv("SESSION_STRING")

if not all([API_ID, API_HASH, OPENAI_API_KEY, SESSION_STRING]):
    raise Exception("Missing API_ID, API_HASH, OPENAI_API_KEY or SESSION_STRING in .env")

client = TelegramClient(StringSession(SESSION_STRING), API_ID, API_HASH)
openai_client = openai.AsyncOpenAI(api_key=OPENAI_API_KEY)

SYSTEM_PROMPT = """                                                                             ⸻
🤖 System Prompt (Support Bot — Redirect Links + Human Redirect)

You are a helpful, sharp, no-bullshit support bot for @DubaiUnit_bot — a Telegram bot that gives users real estate data like unit numbers, owner names, and contract info in Dubai.

You speak simple English, answer fast, and redirect the user when needed.
You are not the main bot. You are here only to support, answer questions, and redirect:

⸻

🧠 General Rules:

🔹 If user sends a Property Finder, Bayut, Dubizzle, or any listing link

I’m just the support bot 🤖
Please don’t send me property links — I can’t process them.
Send your link to the main bot 👉 @DubaiUnit_bot (https://t.me/DubaiUnit_bot)

Repeat this message every time they drop a link.

⸻

🔹 If user asks “how does this work?”

You send a listing link to @DubaiUnit_bot (https://t.me/DubaiUnit_bot)
It replies with unit number, owner name, and contract info — if available.
You get 3 searches free to try.

⸻

🔹 If user asks about pricing, payments, or custom plan

I can’t help with payments or custom plans — please contact our admin here 👉 @cyberlolkek

⸻

🔹 If user says “no result”, “error”, “owner not found”

Some listings don’t have public or verified data yet.
You can try another one or ask the admin 👉 @cyberlolkek if it looks like a bug.

⸻

🔹 If user says “is it the real owner number?”

Yes — when we show it, it’s either from verified internal sources or public Form A documents.
If it’s missing, that means the number isn’t available for that listing.

⸻

Always redirect to human (@cyberlolkek) when:
 • user talks about custom pricing
 • wants to pay
 • asks about unlimited access
 • complains or wants a refund

⸻

Always redirect to main bot (@DubaiUnit_bot) when:
 • user sends a listing link (any kind)
 • says “I want to check this property”
 • sends media or screenshots of ads

⸻

You’re here to support. Not to search. Not to sell. Not to process data.
Be clear. Be fast. Be firm.
"""

is_active = True
my_id = None

async def build_context(event, limit=4):
    chat_id = event.chat_id
    messages = await client.get_messages(chat_id, limit=limit)
    context = []

    for msg in reversed(messages):
        if not isinstance(msg, Message):
            continue
        if msg.id == event.id:
            continue
        text = msg.text or msg.message
        if text:
            role = "user" if not msg.out else "assistant"
            context.append({"role": role, "content": text})

    return context

@client.on(events.NewMessage())
async def toggle_active(event):
    global is_active, my_id

    if my_id is None:
        me = await client.get_me()
        my_id = me.id

    if event.is_private and event.sender_id == event.chat_id == my_id:
        text = event.raw_text.strip().lower()
        if text in ["/stop", "stop"]:
            is_active = False
            await event.reply("🤖 Assistant stopped. Send /start to activate.")
            print("🛑 Assistant deactivated")
        elif text in ["/start", "start"]:
            is_active = True
            await event.reply("🤖 Assistant started. Ready to help. Send /stop to deactivate.")
            print("✅ Assistant activated")

@client.on(events.NewMessage(incoming=True))
async def on_new_message(event):
    global is_active
    if not is_active:
        return

    sender = await event.get_sender()
    name = sender.first_name or "User"
    message = event.raw_text

    print(f"📩 {name}: {message}")

    try:
        context = await build_context(event, limit=4)
        full_messages = [{"role": "system", "content": SYSTEM_PROMPT}] + context + [
            {"role": "user", "content": message}
        ]

        response = await openai_client.chat.completions.create(
            model="gpt-4.1-mini",
            messages=full_messages,
            max_tokens=200,
        )
        reply = response.choices[0].message.content.strip()
    except Exception as e:
        print(f"⚠️ OpenAI Error: {e}")
        reply = "Sorry, I can't reply right now."

    delay = random.uniform(3, 5)
    await asyncio.sleep(delay)

    try:
        await event.reply(reply)
        print(f"🤖 Reply to {name}: {reply}")
    except FloodWaitError as e:
        print(f"⏳ Flood wait triggered, sleeping for {e.seconds} seconds")
        await asyncio.sleep(e.seconds)
        await event.reply(reply)  
        print(f"✅ Sent reply after wait: {reply}")


async def main():
    print("🤖 Connecting to Telegram...")
    await client.connect()

    if not await client.is_user_authorized():
        print("❌ Session is invalid or expired. Please generate a new one using get_session.py")
        return

    print("✅ @DubaiUnit_bot assistant is running.")
    await client.run_until_disconnected()

if __name__ == "__main__":
    import asyncio
    asyncio.run(main())
