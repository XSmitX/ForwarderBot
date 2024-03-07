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

broadcasting = False  # Flag to indicate if broadcasting is ongoing
msg = ""  # Variable to store the message to be broadcasted

@bot.on_message(filters.command('start') & filters.private)
async def start(bot, message):
    await bot.send_message(message.chat.id, "Welcome to Message Forwarder Bot!")

@bot.on_message(filters.command("msg") & filters.private)
async def set_message(bot, message):
    global msg
    if broadcasting:
        await bot.send_message(message.chat.id, "Broadcasting is ongoing. Use /stop to stop it first.")
        return
    msg = message.text.split(maxsplit=1)[1]
    await bot.send_message(message.chat.id, "Message set successfully.")

@bot.on_message(filters.command("stop") & filters.private)
async def stop_broadcast(bot, message):
    global broadcasting, msg
    if broadcasting:
        broadcasting = False
        msg = ""  # Reset the message
        await bot.send_message(message.chat.id, "Broadcasting stopped. Message removed.")
    else:
        await bot.send_message(message.chat.id, "No ongoing broadcasting to stop.")

@bot.on_message(filters.command("add") & filters.private)
async def add_chat_id(bot, message):
    chat_id = int(message.text.split()[1])
    user_id = message.from_user.id
    # Check if user already exists in the database
    user = collection.find_one({"user_id": user_id})
    if user:
        # Update existing user's chat IDs
        collection.update_one({"user_id": user_id}, {"$addToSet": {"chat_ids": chat_id}})
    else:
        # Create new user entry in the database
        collection.insert_one({"user_id": user_id, "chat_ids": [chat_id]})
    await bot.send_message(message.chat.id, f"Chat ID {chat_id} added successfully.")

@bot.on_message(filters.command("broadcast") & filters.private)
async def start_broadcast(bot, message):
    global broadcasting, msg
    if not msg:
        await bot.send_message(message.chat.id, "Message not set. Use /msg command to set a message.")
        return

    if broadcasting:
        await bot.send_message(message.chat.id, "Broadcasting is already ongoing.")
        return

    await bot.send_message(message.chat.id, "Enter time interval in seconds:")

    @bot.on_message(filters.text & filters.private)
    async def set_interval(bot, message):
        global broadcasting, interval
        if not broadcasting:
            try:
                interval = int(message.text)
                broadcasting = True
                await bot.send_message(message.chat.id, f"Broadcasting started with an interval of {interval} seconds.")
                while broadcasting:
                    # Fetch chat IDs from the database
                    chat_ids = get_chat_ids(message.from_user.id)
                    for chat_id in chat_ids:
                        await bot.send_message(chat_id, msg)
                    await asyncio.sleep(interval)
            except ValueError:
                await bot.send_message(message.chat.id, "Invalid input. Please enter a valid number for the time interval.")

def get_chat_ids(user_id):
    user = collection.find_one({"user_id": user_id})
    if user:
        return user["chat_ids"]
    else:
        return []

bot.run()
