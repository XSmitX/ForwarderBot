from pyrogram import Client, filters
from pyrogram.types import Message
import asyncio
import pymongo

# Connect to MongoDB Atlas

mongo_client = pymongo.MongoClient("mongodb+srv://smit:smit@cluster0.pjccvjk.mongodb.net/?retryWrites=true&w=majority")
db = mongo_client["telegram_bot"]
collection = db["users"]

bot = Client(
    "TeBot",
    bot_token="6348649632:AAEJ62K8vK11wbtMNixFh6M2s4-q7O2eBN0",
    api_id=17249531,
    api_hash="b67965c13be2164d8a2bb6d035a1076a"
)


broadcasting_tasks = {}  # Dictionary to store broadcasting tasks for each user
DEFAULT_INTERVAL = 60  # Default interval in seconds

@bot.on_message(filters.command('start') & filters.private)
async def start(bot, message):
    await bot.send_message(message.chat.id, "Welcome to Message Forwarder Bot!")

@bot.on_message(filters.command("msg") & filters.private)
async def set_message(bot, message):
    user_id = message.from_user.id
    msg = message.text.split(maxsplit=1)[1]
    collection.update_one({"user_id": user_id}, {"$set": {"msg": msg}})
    await bot.send_message(message.chat.id, "Message set successfully.")

@bot.on_message(filters.command("add") & filters.private)
async def add_group_id(bot, message):
    group_id = int(message.text.split()[1])
    user_id = message.from_user.id
    # Check if user already exists in the database
    user = collection.find_one({"user_id": user_id})
    if user:
        # Update existing user's group IDs
        collection.update_one({"user_id": user_id}, {"$addToSet": {"group_ids": group_id}})
    else:
        # Create new user entry in the database
        collection.insert_one({"user_id": user_id, "group_ids": [group_id]})
    await bot.send_message(message.chat.id, f"Group ID {group_id} added successfully.")

@bot.on_message(filters.command("broadcast") & filters.private)
async def start_broadcast(bot, message):
    user_id = message.from_user.id
    user = collection.find_one({"user_id": user_id})
    if user:
        group_ids = user.get("group_ids", [])
        if not group_ids:
            await bot.send_message(message.chat.id, "No group IDs added. Use /add to add group IDs.")
            return

        msg = user.get("msg", "")
        if not msg:
            await bot.send_message(message.chat.id, "Message not set. Use /msg command to set a message.")
            return

        if user_id in broadcasting_tasks:
            await bot.send_message(message.chat.id, "Broadcasting is already ongoing for this user.")
            return

        broadcasting_tasks[user_id] = asyncio.create_task(broadcast_message(bot, user_id, group_ids, msg))
        await bot.send_message(message.chat.id, f"Broadcasting started with an interval of {DEFAULT_INTERVAL} seconds.")

@bot.on_message(filters.command("stop") & filters.private)
async def stop_broadcast(bot, message):
    user_id = message.from_user.id
    if user_id in broadcasting_tasks:
        broadcasting_tasks[user_id].cancel()
        del broadcasting_tasks[user_id]
        await bot.send_message(message.chat.id, "Broadcasting stopped.")
    else:
        await bot.send_message(message.chat.id, "No broadcasting task found for this user.")

async def broadcast_message(bot, user_id, group_ids, msg):
    try:
        while True:
            for group_id in group_ids:
                await bot.send_message(group_id, msg)
            await asyncio.sleep(DEFAULT_INTERVAL)
    except asyncio.CancelledError:
        pass

bot.run()
