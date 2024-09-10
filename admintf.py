import json
import os
import requests
from datetime import datetime
from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.triggers.interval import IntervalTrigger
from apscheduler.triggers.date import DateTrigger
from pyrogram import Client, filters
from pyrogram.types import InlineKeyboardButton, InlineKeyboardMarkup, Message
from config import TOKEN as TELEGRAM_BOT_TOKEN, API_ID, API_HASH, ADMIN_BOT_ID, ADMIN_USER_ID

# Initialize the Pyrogram client
app = Client("admin_bot", api_id=API_ID, api_hash=API_HASH, bot_token=TELEGRAM_BOT_TOKEN)
scheduler = BackgroundScheduler()
scheduler.start()

# Helper Functions
def load_json_file(file_path: str) -> list:
    """Load a JSON file and return its content."""
    if os.path.exists(file_path):
        with open(file_path, 'r') as file:
            return json.load(file)
    return []

def save_json_file(file_path: str, data: list) -> None:
    """Save a list to a JSON file."""
    with open(file_path, 'w') as file:
        json.dump(data, file, indent=4)

def load_user_data() -> dict:
    """Load user data from file."""
    return load_json_file('user_data.json')

def load_group_ids() -> list:
    """Load group IDs from file."""
    return load_json_file('group_ids.json')

def load_channel_ids() -> list:
    """Load channel IDs from file."""
    return load_json_file('channel_ids.json')

def load_cloned_bots() -> list:
    """Load cloned bot tokens from file."""
    if os.path.exists('cloned_bots.json'):
        with open('cloned_bots.json', 'r') as file:
            return json.load(file)
    return []

def load_admin_bot_id() -> list:
    """Load admin bot IDs from the configuration file."""
    config_file = 'admin_bot_id.json'
    if os.path.exists(config_file):
        with open(config_file, 'r') as file:
            config_data = json.load(file)
            return config_data.get('admin_bot_id', [])
    return []

def is_admin_bot(user_id: int) -> bool:
    """Check if the user is an admin bot."""
    return user_id == ADMIN_BOT_ID

def is_admin(user_id: int) -> bool:
    """Check if the user is an admin."""
    return user_id == ADMIN_USER_ID

def is_freemium(user_id: int) -> bool:
    """Check if the user is a freemium user."""
    user_data = load_user_data()
    return str(user_id) in user_data and user_data[str(user_id)].get('type') == 'freemium'

def broadcast_message(message_text: str, ids: list, entity_type: str) -> None:
    """Broadcast message to a list of IDs (users, groups, channels)."""
    for entity_id in ids:
        try:
            app.send_message(chat_id=entity_id, text=message_text)
        except Exception as e:
            print(f"Failed to send message to {entity_type} {entity_id}: {e}")

def schedule_broadcast(message_text: str, ids: list, entity_type: str, send_time: datetime) -> None:
    """Schedule a broadcast message."""
    trigger = DateTrigger(run_date=send_time)
    job_func = lambda: broadcast_message(message_text, ids, entity_type)
    scheduler.add_job(job_func, trigger)

def schedule_broadcast_all(message_text: str, interval_hours: int) -> None:
    """Schedule a broadcast message to all freemium users, groups, and channels at specified intervals."""
    job_func = lambda: schedule_all_broadcast(message_text)
    scheduler.add_job(job_func, IntervalTrigger(hours=interval_hours))

def schedule_user_broadcast(message_text: str, interval_hours: int) -> None:
    """Schedule a broadcast message to all freemium users at specified intervals."""
    user_ids = [int(uid) for uid in load_user_data().keys() if is_freemium(int(uid))]
    job_func = lambda: broadcast_message(message_text, user_ids, "user")
    scheduler.add_job(job_func, IntervalTrigger(hours=interval_hours))

def schedule_group_broadcast(message_text: str, interval_hours: int) -> None:
    """Schedule a broadcast message to all freemium groups at specified intervals."""
    group_ids = load_group_ids()
    freemium_groups = [gid for gid in group_ids if any(is_freemium(admin_id) for admin_id in get_admins_of_chat(gid))]
    job_func = lambda: broadcast_message(message_text, freemium_groups, "group")
    scheduler.add_job(job_func, IntervalTrigger(hours=interval_hours))

def schedule_channel_broadcast(message_text: str, interval_hours: int) -> None:
    """Schedule a broadcast message to all freemium channels at specified intervals."""
    channel_ids = load_channel_ids()
    freemium_channels = [cid for cid in channel_ids if any(is_freemium(admin_id) for admin_id in get_admins_of_chat(cid))]
    job_func = lambda: broadcast_message(message_text, freemium_channels, "channel")
    scheduler.add_job(job_func, IntervalTrigger(hours=interval_hours))

def list_scheduled_jobs() -> str:
    """List all scheduled jobs."""
    jobs = scheduler.get_jobs()
    if not jobs:
        return "No scheduled jobs."
    
    job_list = []
    for job in jobs:
        job_info = f"ID: {job.id}, Next run time: {job.next_run_time}, Trigger: {job.trigger}"
        job_list.append(job_info)
    
    return "\n".join(job_list)

def cancel_scheduled_job(job_id: str) -> str:
    """Cancel a scheduled job by its ID."""
    job = scheduler.get_job(job_id)
    if job:
        scheduler.remove_job(job_id)
        return f"Job with ID {job_id} has been canceled."
    else:
        return f"No job found with ID {job_id}."

def set_join_group_or_channel(group_or_channel_id: int) -> None:
    """Set a group or channel ID that users must join to use the bot."""
    join_requirements = load_json_file('join_requirements.json')
    if group_or_channel_id not in join_requirements:
        join_requirements.append(group_or_channel_id)
        save_json_file('join_requirements.json', join_requirements)

def get_join_requirements() -> list:
    """Get a list of group or channel IDs that users must join."""
    return load_json_file('join_requirements.json')

def check_user_joined(user_id: int) -> bool:
    """Check if the user has joined the required group or channel."""
    join_requirements = get_join_requirements()
    
    for group_or_channel_id in join_requirements:
        # Check if the requirement is a group or channel
        if group_or_channel_id.startswith('-100'):
            # It's a group
            try:
                member = app.get_chat_member(chat_id=group_or_channel_id, user_id=user_id)
                if member.status in ['member', 'administrator', 'creator']:
                    return True
            except Exception as e:
                # Handle exception if chat member info cannot be fetched
                print(f"Error checking member status for {user_id} in group {group_or_channel_id}: {e}")
                return False
        else:
            # For channels, we need a different approach
            # Check if user is following the channel (only possible with user bots)
            try:
                response = requests.get(f'https://api.telegram.org/bot{BOT_TOKEN}/getChatMember', params={
                    'chat_id': group_or_channel_id,
                    'user_id': user_id
                })
                result = response.json()
                if result['ok']:
                    status = result['result']['status']
                    if status in ['member', 'administrator', 'creator']:
                        return True
            except requests.RequestException as e:
                # Handle exception if API request fails
                print(f"Error checking channel membership for {user_id} in channel {group_or_channel_id}: {e}")
                return False
    
    return False

@app.on_message(filters.command('broadcastfbot') & filters.user(ADMIN_USER_ID))
def broadcast_to_freemium_bots(client: Client, message: Message) -> None:
    """Broadcast message to all freemium bots."""
    if is_admin(message.from_user.id):
        message_text = ' '.join(message.text.split()[1:])
        broadcast_message(message_text, [int(uid) for uid in load_user_data().keys() if is_freemium(int(uid))], "user")
        client.send_message(message.chat.id, "Broadcast to all freemium bots completed.")
    else:
        client.send_message(message.chat.id, "You do not have permission to use this command.")

@app.on_message(filters.command('broadcastpbot') & filters.user(ADMIN_USER_ID))
def broadcast_to_premium_bots(client: Client, message: Message) -> None:
    """Broadcast message to all premium bots."""
    if is_admin(message.from_user.id):
        message_text = ' '.join(message.text.split()[1:])
        # Replace with your method for getting premium bot IDs
        broadcast_message(message_text, load_cloned_bots(), "bot")
        client.send_message(message.chat.id, "Broadcast to all premium bots completed.")
    else:
        client.send_message(message.chat.id, "You do not have permission to use this command.")

@app.on_message(filters.command('broadcastallbot') & filters.user(ADMIN_USER_ID))
def broadcast_to_all_bots(message_text: str) -> None:
    """Broadcast message to all cloned bots."""
    cloned_bots = load_cloned_bots()
    for bot_token in cloned_bots:
        try:
            bot_client = Client("bot_instance", api_id=API_ID, api_hash=API_HASH, bot_token=bot_token)
            bot_client.send_message(chat_id=bot_id, text=message_text)
        except Exception as e:
            print(f"Failed to send message using bot with token {bot_token}: {e}")

@app.on_message(filters.command('schedule_user') & filters.user(ADMIN_USER_ID))
def handle_schedule_user_broadcast(client: Client, message: Message) -> None:
    """Handle command to schedule broadcasts to all freemium users."""
    if is_admin(message.from_user.id):
        try:
            parts = message.text.split()
            if len(parts) != 3:
                client.send_message(message.chat.id, "Usage: /schedule_user now:<interval_hours>")
                return

            command, now_str, interval_str = parts
            if not now_str.startswith('now:') or not interval_str.isdigit():
                client.send_message(message.chat.id, "Invalid format. Use /schedule_user now:<interval_hours>")
                return
            
            interval_hours = int(interval_str)
            message_text = ' '.join(parts[2:])
            schedule_user_broadcast(message_text, interval_hours)
            client.send_message(message.chat.id, f"Scheduled broadcast to freemium users every {interval_hours} hours.")
        except ValueError:
            client.send_message(message.chat.id, "Invalid input. Please ensure the interval is a number.")
    else:
        client.send_message(message.chat.id, "You do not have permission to schedule broadcasts.")

@app.on_message(filters.command('schedule_group') & filters.user(ADMIN_USER_ID))
def handle_schedule_group_broadcast(client: Client, message: Message) -> None:
    """Handle command to schedule broadcasts to all freemium groups."""
    if is_admin(message.from_user.id):
        try:
            parts = message.text.split()
            if len(parts) != 3:
                client.send_message(message.chat.id, "Usage: /schedule_group now:<interval_hours>")
                return

            command, now_str, interval_str = parts
            if not now_str.startswith('now:') or not interval_str.isdigit():
                client.send_message(message.chat.id, "Invalid format. Use /schedule_group now:<interval_hours>")
                return
            
            interval_hours = int(interval_str)
            message_text = ' '.join(parts[2:])
            schedule_group_broadcast(message_text, interval_hours)
            client.send_message(message.chat.id, f"Scheduled broadcast to freemium groups every {interval_hours} hours.")
        except ValueError:
            client.send_message(message.chat.id, "Invalid input. Please ensure the interval is a number.")
    else:
        client.send_message(message.chat.id, "You do not have permission to schedule broadcasts.")

@app.on_message(filters.command('schedule_channel') & filters.user(ADMIN_USER_ID))
def handle_schedule_channel_broadcast(client: Client, message: Message) -> None:
    """Handle command to schedule broadcasts to all freemium channels."""
    if is_admin(message.from_user.id):
        try:
            parts = message.text.split()
            if len(parts) != 3:
                client.send_message(message.chat.id, "Usage: /schedule_channel now:<interval_hours>")
                return

            command, now_str, interval_str = parts
            if not now_str.startswith('now:') or not interval_str.isdigit():
                client.send_message(message.chat.id, "Invalid format. Use /schedule_channel now:<interval_hours>")
                return
            
            interval_hours = int(interval_str)
            message_text = ' '.join(parts[2:])
            schedule_channel_broadcast(message_text, interval_hours)
            client.send_message(message.chat.id, f"Scheduled broadcast to freemium channels every {interval_hours} hours.")
        except ValueError:
            client.send_message(message.chat.id, "Invalid input. Please ensure the interval is a number.")
    else:
        client.send_message(message.chat.id, "You do not have permission to schedule broadcasts.")

@app.on_message(filters.command('schedule_all') & filters.user(ADMIN_USER_ID))
def handle_schedule_all_broadcast(client: Client, message: Message) -> None:
    """Handle command to schedule broadcasts to all freemium users, groups, and channels."""
    if is_admin(message.from_user.id):
        try:
            parts = message.text.split()
            if len(parts) != 3:
                client.send_message(message.chat.id, "Usage: /schedule_all now:<interval_hours>")
                return

            command, now_str, interval_str = parts
            if not now_str.startswith('now:') or not interval_str.isdigit():
                client.send_message(message.chat.id, "Invalid format. Use /schedule_all now:<interval_hours>")
                return
            
            interval_hours = int(interval_str)
            message_text = ' '.join(parts[2:])
            schedule_broadcast_all(message_text, interval_hours)
            client.send_message(message.chat.id, f"Scheduled broadcast to freemium users, groups, and channels every {interval_hours} hours.")
        except ValueError:
            client.send_message(message.chat.id, "Invalid input. Please ensure the interval is a number.")
    else:
        client.send_message(message.chat.id, "You do not have permission to schedule broadcasts.")

@app.on_message(filters.command('list_scheduled') & filters.user(ADMIN_USER_ID))
def handle_list_scheduled_jobs(client: Client, message: Message) -> None:
    """Handle command to list all scheduled jobs."""
    if is_admin(message.from_user.id):
        job_list = list_scheduled_jobs()
        client.send_message(message.chat.id, f"Scheduled Jobs:\n{job_list}")
    else:
        client.send_message(message.chat.id, "You do not have permission to use this command.")

@app.on_message(filters.command('cancel_schedule') & filters.user(ADMIN_USER_ID))
def handle_cancel_scheduled_job(client: Client, message: Message) -> None:
    """Handle command to cancel a scheduled job by ID."""
    if is_admin(message.from_user.id):
        try:
            _, job_id = message.text.split()
            result = cancel_scheduled_job(job_id)
            client.send_message(message.chat.id, result)
        except ValueError:
            client.send_message(message.chat.id, "Usage: /cancel_schedule <job_id>")
    else:
        client.send_message(message.chat.id, "You do not have permission to use this command.")

@app.on_message(filters.command('setjoin') & filters.user(ADMIN_USER_ID))
def handle_set_join(client: Client, message: Message) -> None:
    """Handle command to set a group or channel that users must join to use the bot."""
    if is_admin(message.from_user.id):
        try:
            _, group_or_channel_id = message.text.split()
            group_or_channel_id = int(group_or_channel_id)
            set_join_group_or_channel(group_or_channel_id)
            client.send_message(message.chat.id, f"Group or channel with ID {group_or_channel_id} set as required for joining.")
        except ValueError:
            client.send_message(message.chat.id, "Usage: /setjoin <group_or_channel_id>")
    else:
        client.send_message(message.chat.id, "You do not have permission to use this command.")

@app.on_message(filters.private & ~filters.user(ADMIN_USER_ID))
def handle_user_not_joined(client: Client, message: Message) -> None:
    """Handle messages from users who have not joined the required group or channel."""
    if not check_user_joined(message.from_user.id):
        join_requirements = get_join_requirements()
        if join_requirements:
            join_button = InlineKeyboardButton(text="Join Required Group/Channel", url=f"https://t.me/{join_requirements[0]}")
            keyboard = InlineKeyboardMarkup([[join_button]])
            client.send_message(message.chat.id, "You need to join the required group or channel before using this bot. Please join using the button below:", reply_markup=keyboard)
        else:
            client.send_message(message.chat.id, "Access to this bot is restricted until you join the required group or channel.")

# Start the Pyrogram client
if __name__ == "__main__":
    app.run()
