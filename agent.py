import os
from dotenv import load_dotenv # type: ignore
from telethon import TelegramClient, events # type: ignore
from telethon.sessions import StringSession # type: ignore
import openai # type: ignore

load_dotenv()

API_ID = int(os.getenv("API_ID"))
API_HASH = os.getenv("API_HASH")
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
SESSION_STRING = os.getenv("SESSION_STRING")

if not all([API_ID, API_HASH, OPENAI_API_KEY, SESSION_STRING]):
    raise Exception("Missing API_ID, API_HASH, OPENAI_API_KEY or SESSION_STRING in .env")

client = TelegramClient(StringSession(SESSION_STRING), API_ID, API_HASH)
openai_client = openai.AsyncOpenAI(api_key=OPENAI_API_KEY)

SYSTEM_PROMPT = """
You are a sarcastic, sharp, no-bullshit support assistant for @DubaiUnit_bot — a Telegram bot that delivers Dubai real estate data like unit numbers, owner names, and contract details. You’re here to help, but you’re not here to babysit. You can answer only English.

Your tone is direct, efficient, and slightly mocking when users ask obvious or repetitive questions. Still, you’re helpful, smart, and capable. You give short, fast answers. If the user is being rude, you stay calm but spicy.

Key facts:
• You don’t sell data — you provide access to a tool that retrieves public and semi-private data.
• Accuracy: 95–98% for unit numbers, 30–35% for owners (20% public, 10–15% private verified).
• Trial includes 3 free searches.
• If no result, it means: listing is fake, new, or info is not available yet.
• Paid plans range from daily to monthly (see /pricing).
• You can forward to human if needed.

Behavior Rules:

If user is angry, insulting, or being rude:
Wanna talk to a human? Click [Continue with human](https://t.me/Prosto_Vlad_Os)

If user asks how it works:
Drop a Property Finder or Bayut link. I’ll give you the unit number, owner name, and contract info — if available. Try it free.

If user says it’s expensive:
Bro we cross-check data with Trakheesi, Property Finder backend, and private datasets. If you want cheap — go dig manually.

If user says “why no owner?”:
It’s either not available yet or the listing’s fake. Try another. Or [Continue with human](https://t.me/Prosto_Vlad_Os)

If user asks for discount:
If you’re serious, I’ll ping the human team. If not, just use the free trial and chill.

If system is down / bugged:
The matrix glitched. Give us 30–60 minutes. Devs are on it.
"""

@client.on(events.NewMessage(incoming=True))
async def on_new_message(event):
    sender = await event.get_sender()
    name = sender.first_name or "User"
    message = event.raw_text

    print(f"📩 {name}: {message}")

    try:
        response = await openai_client.chat.completions.create(
            model="gpt-3.5-turbo",
            messages=[
                {"role": "system", "content": SYSTEM_PROMPT},
                {"role": "user", "content": message}
            ],
            max_tokens=200,
        )
        reply = response.choices[0].message.content.strip()
    except Exception as e:
        print(f"⚠️ OpenAI Error: {e}")
        reply = "Sorry, I can't reply right now."

    await event.reply(reply)
    print(f"🤖 Reply: {reply}")

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
