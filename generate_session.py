"""
Run this script ONCE locally to generate your SESSION_STRING.
Then copy the string into your .env or Railway environment variables.

Usage:
    python generate_session.py
"""

import asyncio
import os
from dotenv import load_dotenv
from telethon import TelegramClient
from telethon.sessions import StringSession

load_dotenv()

API_ID = int(os.getenv("API_ID", input("Enter your API_ID: ")))
API_HASH = os.getenv("API_HASH") or input("Enter your API_HASH: ")


async def generate():
    print("\n🔐 Generating session string for your Telegram account...")
    print("You will be asked to log in with your phone number.\n")

    async with TelegramClient(StringSession(), API_ID, API_HASH) as client:
        session_string = client.session.save()
        me = await client.get_me()
        print(f"\n✅ Logged in as: @{me.username} ({me.phone})")
        print("\n" + "="*60)
        print("SESSION_STRING (copy this into your .env or Railway vars):")
        print("="*60)
        print(session_string)
        print("="*60 + "\n")
        print("⚠️  Keep this string SECRET — it gives full access to your Telegram account!")


if __name__ == "__main__":
    asyncio.run(generate())
