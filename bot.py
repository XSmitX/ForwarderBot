from pyrogram import Client, filters
from pyrogram.types import Message
import asyncio
import pymongo
from pyrogram.enums import ChatMemberStatus
from pyrogram.types import InlineKeyboardButton as ikb, InlineKeyboardMarkup as ikm
# Connect to MongoDB Atlas

mongo_client = pymongo.MongoClient("mongodb+srv://smit:smit@cluster0.pjccvjk.mongodb.net/?retryWrites=true&w=majority")
db = mongo_client["telegram_bot"]
collection = db["users"]
chat_ids_collection = db["chat_ids"]
premium_collection = db["premium"]

bot = Client(
    "TeBofsdfsf",
    bot_token="6348649632:AAEJ62K8vK11wbtMNixFh6M2s4-q7O2eBN0",
    api_id=17249531,
    api_hash="b67965c13be2164d8a2bb6d035a1076a"
)


channel_username = "@Sam_Ott_Store"

def check_joined():
    async def func(flt, bot, message):
        join_msg = f"**To use this bot, Please join our channel.\nJoin From The Link Below 👇**"
        user_idd = message.from_user.id
        chat_idd = message.chat.id
        try:
            member_info = await bot.get_chat_member(channel_username, user_idd)
            if member_info.status in (ChatMemberStatus.OWNER, ChatMemberStatus.ADMINISTRATOR, ChatMemberStatus.MEMBER):
                return True
            else:
                await bot.send_message(chat_idd, join_msg , reply_markup=ikm([[ikb("✅ Join Channel", url=f"https://t.me/Sam_Ott_Store")]]))
                return False
        except Exception as e:
            await bot.send_message(chat_idd, join_msg , reply_markup=ikm([[ikb("✅ Join Channel", url="https://t.me/Sam_Ott_Store")]]))
            return False

    return filters.create(func)

ADMIN_ID = [6121699672, 6971497666]
# Dictionary to store broadcasting tasks for each user
broadcasting_tasks = {}
# Default interval in seconds
DEFAULT_INTERVAL = 300

@bot.on_message(filters.command('start') & check_joined())
async def start(bot, message):
    if check_joined():
        user_id = message.from_user.id
        if not collection.find_one({"user_id": user_id}):
            collection.insert_one({"user_id": user_id})
        await bot.send_message(message.chat.id, "Welcome to Message Forwarder Bot!")


@bot.on_message(filters.command("msg") & filters.private)
async def set_message(bot, message):
    user_id = message.from_user.id
    msg = message.text.split(maxsplit=1)[1]
    collection.update_one({"user_id": user_id}, {"$set": {"msg": msg}})
    await bot.send_message(message.chat.id, "Message set successfully.")

@bot.on_message(filters.command("add") & filters.private)
async def add_chat_id(bot, message):
    user_id = message.from_user.id 
    if message.from_user.id not in ADMIN_ID:
        await bot.send_message(message.chat.id, "Only the admin can add chat IDs.")
        return
    chat_id = int(message.text.split()[1])
    chat_ids_collection.insert_one({"chat_id": chat_id})
    await bot.send_message(message.chat.id, f"Chat ID {chat_id} added successfully.")
 #   if user_id == ADMIN_ID:
 #       chat_id = int(message.text.split()[1])
 #       chat_ids_collection.insert_one({"chat_id": chat_id})
 #       await bot.send_message(message.chat.id, f"Chat ID {chat_id} added successfully.")
 #   else:
 #       await bot.send_message(message.chat.id, "Only the admin can add chat IDs.")
@bot.on_message(filters.command("adduser") & filters.private)
async def add_user_to_premium(bot, message):
    user_id = message.from_user.id
    if user_id not in ADMIN_ID:
        await bot.send_message(message.chat.id, "Only the admin can add users to premium.")
        return
    try:
        user_to_add_id = int(message.text.split()[1])
        if premium_collection.find_one({"user_id": user_to_add_id}):
            await bot.send_message(message.chat.id, f"User {user_to_add_id} is already a premium user.")
        else:
            premium_collection.insert_one({"user_id": user_to_add_id})
            await bot.send_message(message.chat.id, f"User {user_to_add_id} added to premium.")
    except ValueError:
        await bot.send_message(message.chat.id, "Invalid user ID provided.")
 
@bot.on_message(filters.command("removeuser") & filters.private)
async def remove_user_from_premium(bot, message):
    user_id = message.from_user.id
    if user_id not in ADMIN_ID:
        await bot.send_message(message.chat.id, "Only the admin can remove users.")
        return
    try:
        user_to_remove_id = int(message.text.split()[1])
        deleted_count = premium_collection.delete_many({"user_id": user_to_remove_id}).deleted_count
        if deleted_count:
            await bot.send_message(message.chat.id, f"User {user_to_remove_id} removed from premium.")
        else:
            await bot.send_message(message.chat.id, f"User {user_to_remove_id} not found in premium users list.")
    except ValueError:
        await bot.send_message(message.chat.id, "Invalid user ID provided.")

@bot.on_message(filters.command("stats") & filters.private)
async def premium_users_stats(bot, message):
    if message.from_user.id not in ADMIN_ID:
        await bot.send_message(message.chat.id, "Only the admin can view stats.")
        return
    premium_users = premium_collection.find()
    count_users = premium_collection.count_documents({})
    users_list = "\n".join([str(user["user_id"]) for user in premium_users])
    if users_list:
        await bot.send_message(message.chat.id, f"Total Premium Users: {count_users}\n\nPremium Users List:\n{users_list}")
    else:
        await bot.send_message(message.chat.id, "No premium users found.")


@bot.on_message(filters.command("broadcast") & filters.private & check_joined())
async def start_broadcast(bot, message):
    user_id = message.from_user.id
    if is_user_premium(user_id):
        user = collection.find_one({"user_id": user_id})
        if user:
            chat_ids = [chat["chat_id"] for chat in chat_ids_collection.find()]
            if not chat_ids:
                await bot.send_message(message.chat.id, "No chat IDs added.")
                return

            msg = user.get("msg", "")
            if not msg:
                await bot.send_message(message.chat.id, "Message not set. Use /msg command to set a message.")
                return

            if user_id in broadcasting_tasks:
                await bot.send_message(message.chat.id, "Broadcasting is already ongoing for this user.")
                return

            broadcasting_tasks[user_id] = asyncio.create_task(broadcast_message(bot, user_id, chat_ids, msg))
            await bot.send_message(message.chat.id, f"Broadcasting started with an interval of {DEFAULT_INTERVAL} seconds.")
            # Inform the user that broadcasting has started
            await bot.send_message(user_id, "Broadcasting started.")
    else:
        await bot.send_message(message.chat.id, f"You are not a premium user. \nContact @Sam_Hub_Op to upgrade to premium.\nYour User id is : <code>{user_id}</code>")

@bot.on_message(filters.command("stop") & filters.private)
async def stop_broadcast(bot, message):
    user_id = message.from_user.id
    if user_id in broadcasting_tasks:
        broadcasting_tasks[user_id].cancel()
        del broadcasting_tasks[user_id]
        await bot.send_message(message.chat.id, "Broadcasting stopped.")
    else:
        await bot.send_message(message.chat.id, "No broadcasting task found for this user.")

def is_user_premium(user_id):
    return premium_collection.find_one({"user_id": user_id}) is not None

async def broadcast_message(bot, user_id, chat_ids, msg):
  # Counter for successful message sends
    try:
        while True:
            successful_sends = 0
            for chat_id in chat_ids:
                try:
                    await bot.send_message(chat_id, msg)
                    successful_sends += 1
                except:
                    print(f"Failed to send message to chat {chat_id}. Skipping...")
            await bot.send_message(user_id, f"Message sent to {successful_sends} groups.")
            await asyncio.sleep(DEFAULT_INTERVAL)
    except asyncio.CancelledError:
        pass
    # Send notification to user about the number of successful sends
    #await bot.send_message(user_id, f"Message sent to {successful_sends} groups.")
@bot.on_message(filters.command("msgall") & filters.private)
async def broadcast_message(bot, message: Message):
    # Check if user is admin
    if message.from_user.id not in ADMIN_ID:
        await message.reply_text("You are not authorized to use this command.")
        return

    # If the user replied to a text message
    if message.reply_to_message and message.reply_to_message.text:
        # Extract the text
        msg = message.reply_to_message.text
    else:
        await message.reply_text("You need to reply to a text message to broadcast it.")
        return

    # Get all users using the bot
    users = premium_collection.find({})

    total_users = 0
    success_count = 0
    error_count = 0

    # Count total number of users
    total_users = premium_collection.count_documents({})
    print(f"Total number of users: {total_users}")

    await message.reply_text("Broadcasting...")

    # Send the message to all users
    for user in users:
        try:
            # Broadcasting the text message without parse_mode
            await bot.send_message(user['user_id'], msg)
            success_count += 1
        except Exception as e:
            error_count += 1
            print(f"Failed to send broadcast message to user {user['user_id']}: {e}")

    await message.reply_text(f"Broadcast message sent to {success_count} users with {error_count} errors.")

bot.run()
