import json
import os
import telebot
from typing import List, Dict
from datetime import datetime
from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.triggers.date import DateTrigger
from config import TOKEN as TELEGRAM_BOT_TOKEN, ADMIN_USER_ID, ALLOWED_USER_IDS

# Initialize bot with API token
bot = telebot.TeleBot(TELEGRAM_BOT_TOKEN)
scheduler = BackgroundScheduler()
scheduler.start()

# Helper Functions
def load_json_file(file_path: str) -> List[int]:
    """Load a JSON file and return its content as a list."""
    if os.path.exists(file_path):
        with open(file_path, 'r') as file:
            return json.load(file)
    return []

def load_user_data() -> dict:
    """Load user data from file."""
    return load_json_file('user_data.json')

def load_group_ids() -> List[int]:
    """Load group IDs from file."""
    return load_json_file('group_ids.json')

def load_channel_ids() -> List[int]:
    """Load channel IDs from file."""
    return load_json_file('channel_ids.json')

def is_admin(user_id: int) -> bool:
    """Check if the user is an admin."""
    return user_id == ADMIN_USER_ID

def is_freemium(user_id: int) -> bool:
    """Check if the user is a freemium user."""
    user_data = load_user_data()
    return str(user_id) in user_data and user_data[str(user_id)].get('subscription_end') is None

def is_premium(user_id: int) -> bool:
    """Check if the user is a premium user."""
    user_data = load_user_data()
    return str(user_id) in user_data and user_data[str(user_id)].get('subscription_end') is not None

def get_admins_of_chat(chat_id: int) -> List[int]:
    """Retrieve the list of admins for a chat."""
    try:
        admins = bot.get_chat_administrators(chat_id)
        return [admin.user.id for admin in admins]
    except Exception as e:
        print(f"Failed to get admins of chat {chat_id}: {e}")
        return []

def broadcast_message(message_text: str, ids: List[int], entity_type: str) -> None:
    """Broadcast message to a list of IDs (users, groups, channels)."""
    for entity_id in ids:
        try:
            bot.send_message(chat_id=entity_id, text=message_text)
        except Exception as e:
            print(f"Failed to send message to {entity_type} {entity_id}: {e}")

def schedule_broadcast(message_text: str, ids: List[int], entity_type: str, send_time: datetime) -> None:
    """Schedule a broadcast message."""
    trigger = DateTrigger(run_date=send_time)
    job_func = lambda: broadcast_message(message_text, ids, entity_type)
    scheduler.add_job(job_func, trigger)

def schedule_all_broadcast(message_text: str, send_time: datetime) -> None:
    """Schedule a broadcast message to all users, groups, and channels."""
    user_data = load_user_data()
    freemium_users = [int(uid) for uid in user_data.keys() if is_freemium(int(uid))]
    group_ids = load_group_ids()
    channel_ids = load_channel_ids()

    # Schedule broadcasts for users
    schedule_broadcast(message_text, freemium_users, "user", send_time)

    # Schedule broadcasts for groups where bot admin is freemium
    freemium_groups = [gid for gid in group_ids if any(is_freemium(admin_id) for admin_id in get_admins_of_chat(gid))]
    schedule_broadcast(message_text, freemium_groups, "group", send_time)

    # Schedule broadcasts for channels where bot admin is freemium
    freemium_channels = [cid for cid in channel_ids if any(is_freemium(admin_id) for admin_id in get_admins_of_chat(cid))]
    schedule_broadcast(message_text, freemium_channels, "channel", send_time)

# Command Handlers
@bot.message_handler(commands=['broadcast_user'])
def broadcast_to_user(message: telebot.types.Message) -> None:
    """Broadcast message to all users."""
    message_text = ' '.join(message.text.split()[1:])
    user_data = load_user_data()
    freemium_users = [int(uid) for uid in user_data.keys() if is_freemium(int(uid))]
    broadcast_message(message_text, freemium_users, "user")
    bot.reply_to(message, "Broadcast to all users completed.")

@bot.message_handler(commands=['broadcast_group'])
def broadcast_to_group(message: telebot.types.Message) -> None:
    """Broadcast message to groups."""
    message_text = ' '.join(message.text.split()[1:])
    group_ids = load_group_ids()
    freemium_groups = [gid for gid in group_ids if any(is_freemium(admin_id) for admin_id in get_admins_of_chat(gid))]
    broadcast_message(message_text, freemium_groups, "group")
    bot.reply_to(message, "Broadcast to all groups completed.")

@bot.message_handler(commands=['broadcast_channel'])
def broadcast_to_channel(message: telebot.types.Message) -> None:
    """Broadcast message to channels."""
    message_text = ' '.join(message.text.split()[1:])
    channel_ids = load_channel_ids()
    freemium_channels = [cid for cid in channel_ids if any(is_freemium(admin_id) for admin_id in get_admins_of_chat(cid))]
    broadcast_message(message_text, freemium_channels, "channel")
    bot.reply_to(message, "Broadcast to all channels completed.")

@bot.message_handler(commands=['broadcast_all'])
def broadcast_to_all(message: telebot.types.Message) -> None:
    """Broadcast message to all users, groups, and channels."""
    message_text = ' '.join(message.text.split()[1:])
    user_data = load_user_data()
    freemium_users = [int(uid) for uid in user_data.keys() if is_freemium(int(uid))]
    group_ids = load_group_ids()
    channel_ids = load_channel_ids()

    # Broadcast to users
    broadcast_message(message_text, freemium_users, "user")

    # Broadcast to groups
    freemium_groups = [gid for gid in group_ids if any(is_freemium(admin_id) for admin_id in get_admins_of_chat(gid))]
    broadcast_message(message_text, freemium_groups, "group")

    # Broadcast to channels
    freemium_channels = [cid for cid in channel_ids if any(is_freemium(admin_id) for admin_id in get_admins_of_chat(cid))]
    broadcast_message(message_text, freemium_channels, "channel")

    bot.reply_to(message, "Broadcast to all users, groups, and channels completed.")

@bot.message_handler(commands=['schedule_user'])
def schedule_user_broadcast(message: telebot.types.Message) -> None:
    """Schedule broadcast message to all users."""
    if is_admin(message.from_user.id):
        try:
            _, datetime_str, *message_parts = message.text.split()
            message_text = ' '.join(message_parts)
            send_time = datetime.fromisoformat(datetime_str)
            user_data = load_user_data()
            freemium_users = [int(uid) for uid in user_data.keys() if is_freemium(int(uid))]
            schedule_broadcast(message_text, freemium_users, "user", send_time)
            bot.reply_to(message, f"Scheduled broadcast to all users at {send_time}.")
        except ValueError:
            bot.reply_to(message, "Invalid date format. Please use ISO format (e.g., 2024-09-01T12:00:00).")
    else:
        bot.reply_to(message, "You do not have permission to schedule broadcasts.")

@bot.message_handler(commands=['schedule_group'])
def schedule_group_broadcast(message: telebot.types.Message) -> None:
    """Schedule broadcast message to all groups."""
    if is_admin(message.from_user.id):
        try:
            _, datetime_str, *message_parts = message.text.split()
            message_text = ' '.join(message_parts)
            send_time = datetime.fromisoformat(datetime_str)
            group_ids = load_group_ids()
            freemium_groups = [gid for gid in group_ids if any(is_freemium(admin_id) for admin_id in get_admins_of_chat(gid))]
            schedule_broadcast(message_text, freemium_groups, "group", send_time)
            bot.reply_to(message, f"Scheduled broadcast to all groups at {send_time}.")
        except ValueError:
            bot.reply_to(message, "Invalid date format. Please use ISO format (e.g., 2024-09-01T12:00:00).")
    else:
        bot.reply_to(message, "You do not have permission to schedule broadcasts.")

@bot.message_handler(commands=['schedule_channel'])
def schedule_channel_broadcast(message: telebot.types.Message) -> None:
    """Schedule broadcast message to all channels."""
    if is_admin(message.from_user.id):
        try:
            _, datetime_str, *message_parts = message.text.split()
            message_text = ' '.join(message_parts)
            send_time = datetime.fromisoformat(datetime_str)
            channel_ids = load_channel_ids()
            freemium_channels = [cid for cid in channel_ids if any(is_freemium(admin_id) for admin_id in get_admins_of_chat(cid))]
            schedule_broadcast(message_text, freemium_channels, "channel", send_time)
            bot.reply_to(message, f"Scheduled broadcast to all channels at {send_time}.")
        except ValueError:
            bot.reply_to(message, "Invalid date format. Please use ISO format (e.g., 2024-09-01T12:00:00).")
    else:
        bot.reply_to(message, "You do not have permission to schedule broadcasts.")

@bot.message_handler(commands=['schedule_all'])
def schedule_all_broadcast(message: telebot.types.Message) -> None:
    """Schedule a broadcast message to all users, groups, and channels."""
    if is_admin(message.from_user.id):
        try:
            _, datetime_str, *message_parts = message.text.split()
            message_text = ' '.join(message_parts)
            send_time = datetime.fromisoformat(datetime_str)
            schedule_all_broadcast(message_text, send_time)
            bot.reply_to(message, f"Scheduled broadcast to all users, groups, and channels at {send_time}.")
        except ValueError:
            bot.reply_to(message, "Invalid date format. Please use ISO format (e.g., 2024-09-01T12:00:00).")
    else:
        bot.reply_to(message, "You do not have permission to schedule broadcasts.")

# Polling the bot
bot.polling(none_stop=True)
