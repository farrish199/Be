import json
import os
import telebot
import requests
from datetime import datetime
from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.triggers.interval import IntervalTrigger
from apscheduler.triggers.date import DateTrigger
from config import TOKEN as TELEGRAM_BOT_TOKEN, ADMIN_BOT_ID

# Initialize bot with API token
bot = telebot.TeleBot(TELEGRAM_BOT_TOKEN)
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

def is_admin_bot(user_id: int) -> bool:
    """Check if the user is an admin bot."""
    return user_id == ADMIN_BOT_ID

def is_freemium(user_id: int) -> bool:
    """Check if the user is a freemium user."""
    return user_id in load_user_data() and load_user_data()[str(user_id)].get('type') == 'freemium'

def get_admins_of_chat(chat_id: int) -> list:
    """Get a list of admins of a chat."""
    # Implement function to get chat admins
    pass

def broadcast_message(message_text: str, ids: list, entity_type: str) -> None:
    """Broadcast message to a list of IDs (users, groups, channels)."""
    for entity_id in ids:
        try:
            bot.send_message(chat_id=entity_id, text=message_text)
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
    job_func = lambda: broadcast_message(message_text, [int(uid) for uid in load_user_data().keys() if is_freemium(int(uid))], "user")
    scheduler.add_job(job_func, IntervalTrigger(hours=interval_hours))

def schedule_group_broadcast(message_text: str, interval_hours: int) -> None:
    """Schedule a broadcast message to all freemium groups at specified intervals."""
    freemium_groups = [gid for gid in load_group_ids() if any(is_freemium(admin_id) for admin_id in get_admins_of_chat(gid))]
    job_func = lambda: broadcast_message(message_text, freemium_groups, "group")
    scheduler.add_job(job_func, IntervalTrigger(hours=interval_hours))

def schedule_channel_broadcast(message_text: str, interval_hours: int) -> None:
    """Schedule a broadcast message to all freemium channels at specified intervals."""
    freemium_channels = [cid for cid in load_channel_ids() if any(is_freemium(admin_id) for admin_id in get_admins_of_chat(cid))]
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
                member = bot.get_chat_member(chat_id=group_or_channel_id, user_id=user_id)
                if member.status in ['member', 'administrator', 'creator']:
                    return True
            except telebot.apihelper.ApiException:
                # Handle exception if chat member info cannot be fetched
                return False
        else:
            # For channels, we need a different approach
            # Check if user is following the channel (only possible with user bots)
            try:
                response = requests.get(f'https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/getChatMember', params={
                    'chat_id': group_or_channel_id,
                    'user_id': user_id
                })
                result = response.json()
                if result['ok']:
                    status = result['result']['status']
                    if status in ['member', 'administrator', 'creator']:
                        return True
            except requests.RequestException:
                # Handle exception if API request fails
                return False
    
    return False

# Command Handlers
@bot.message_handler(commands=['broadcastallbot'])
def broadcast_to_all_bots(message: telebot.types.Message) -> None:
    """Broadcast message to all cloned bots."""
    if is_admin_bot(message.from_user.id):
        message_text = ' '.join(message.text.split()[1:])
        send_message_to_cloned_bots(message_text)
        bot.reply_to(message, "Broadcast to all cloned bots completed.")
    else:
        bot.reply_to(message, "You do not have permission to use this command.")

@bot.message_handler(commands=['broadcastfbot'])
def broadcast_to_freemium_bots(message: telebot.types.Message) -> None:
    """Broadcast message to all freemium bots."""
    if is_admin_bot(message.from_user.id):
        message_text = ' '.join(message.text.split()[1:])
        send_message_to_freemium_bots(message_text)
        bot.reply_to(message, "Broadcast to all freemium bots completed.")
    else:
        bot.reply_to(message, "You do not have permission to use this command.")

@bot.message_handler(commands=['broadcastpbot'])
def broadcast_to_premium_bots(message: telebot.types.Message) -> None:
    """Broadcast message to all premium bots."""
    if is_admin_bot(message.from_user.id):
        message_text = ' '.join(message.text.split()[1:])
        send_message_to_premium_bots(message_text)
        bot.reply_to(message, "Broadcast to all premium bots completed.")
    else:
        bot.reply_to(message, "You do not have permission to use this command.")

@bot.message_handler(commands=['schedule_user'])
def handle_schedule_user_broadcast(message: telebot.types.Message) -> None:
    """Handle command to schedule broadcasts to all freemium users."""
    if is_admin_bot(message.from_user.id):
        try:
            parts = message.text.split()
            if len(parts) != 3:
                bot.reply_to(message, "Usage: /schedule_user now:<interval_hours>")
                return

            command, now_str, interval_str = parts
            if not now_str.startswith('now:') or not interval_str.isdigit():
                bot.reply_to(message, "Invalid format. Use /schedule_user now:<interval_hours>")
                return
            
            interval_hours = int(interval_str)
            message_text = ' '.join(parts[2:])
            schedule_user_broadcast(message_text, interval_hours)
            bot.reply_to(message, f"Scheduled broadcast to freemium users every {interval_hours} hours.")
        except ValueError:
            bot.reply_to(message, "Invalid input. Please ensure the interval is a number.")
    else:
        bot.reply_to(message, "You do not have permission to schedule broadcasts.")

@bot.message_handler(commands=['schedule_group'])
def handle_schedule_group_broadcast(message: telebot.types.Message) -> None:
    """Handle command to schedule broadcasts to all freemium groups."""
    if is_admin_bot(message.from_user.id):
        try:
            parts = message.text.split()
            if len(parts) != 3:
                bot.reply_to(message, "Usage: /schedule_group now:<interval_hours>")
                return

            command, now_str, interval_str = parts
            if not now_str.startswith('now:') or not interval_str.isdigit():
                bot.reply_to(message, "Invalid format. Use /schedule_group now:<interval_hours>")
                return
            
            interval_hours = int(interval_str)
            message_text = ' '.join(parts[2:])
            schedule_group_broadcast(message_text, interval_hours)
            bot.reply_to(message, f"Scheduled broadcast to freemium groups every {interval_hours} hours.")
        except ValueError:
            bot.reply_to(message, "Invalid input. Please ensure the interval is a number.")
    else:
        bot.reply_to(message, "You do not have permission to schedule broadcasts.")

@bot.message_handler(commands=['schedule_channel'])
def handle_schedule_channel_broadcast(message: telebot.types.Message) -> None:
    """Handle command to schedule broadcasts to all freemium channels."""
    if is_admin_bot(message.from_user.id):
        try:
            parts = message.text.split()
            if len(parts) != 3:
                bot.reply_to(message, "Usage: /schedule_channel now:<interval_hours>")
                return

            command, now_str, interval_str = parts
            if not now_str.startswith('now:') or not interval_str.isdigit():
                bot.reply_to(message, "Invalid format. Use /schedule_channel now:<interval_hours>")
                return
            
            interval_hours = int(interval_str)
            message_text = ' '.join(parts[2:])
            schedule_channel_broadcast(message_text, interval_hours)
            bot.reply_to(message, f"Scheduled broadcast to freemium channels every {interval_hours} hours.")
        except ValueError:
            bot.reply_to(message, "Invalid input. Please ensure the interval is a number.")
    else:
        bot.reply_to(message, "You do not have permission to schedule broadcasts.")

@bot.message_handler(commands=['schedule_all'])
def handle_schedule_all_broadcast(message: telebot.types.Message) -> None:
    """Handle command to schedule broadcasts to all freemium users, groups, and channels."""
    if is_admin_bot(message.from_user.id):
        try:
            parts = message.text.split()
            if len(parts) != 3:
                bot.reply_to(message, "Usage: /schedule_all now:<interval_hours>")
                return

            command, now_str, interval_str = parts
            if not now_str.startswith('now:') or not interval_str.isdigit():
                bot.reply_to(message, "Invalid format. Use /schedule_all now:<interval_hours>")
                return
            
            interval_hours = int(interval_str)
            message_text = ' '.join(parts[2:])
            schedule_broadcast_all(message_text, interval_hours)
            bot.reply_to(message, f"Scheduled broadcast to freemium users, groups, and channels every {interval_hours} hours.")
        except ValueError:
            bot.reply_to(message, "Invalid input. Please ensure the interval is a number.")
    else:
        bot.reply_to(message, "You do not have permission to schedule broadcasts.")

@bot.message_handler(commands=['list_scheduled'])
def handle_list_scheduled_jobs(message: telebot.types.Message) -> None:
    """Handle command to list all scheduled jobs."""
    if is_admin_bot(message.from_user.id):
        job_list = list_scheduled_jobs()
        bot.reply_to(message, f"Scheduled Jobs:\n{job_list}")
    else:
        bot.reply_to(message, "You do not have permission to use this command.")

@bot.message_handler(commands=['cancel_schedule'])
def handle_cancel_scheduled_job(message: telebot.types.Message) -> None:
    """Handle command to cancel a scheduled job by ID."""
    if is_admin_bot(message.from_user.id):
        try:
            _, job_id = message.text.split()
            result = cancel_scheduled_job(job_id)
            bot.reply_to(message, result)
        except ValueError:
            bot.reply_to(message, "Usage: /cancel_schedule <job_id>")
    else:
        bot.reply_to(message, "You do not have permission to use this command.")

@bot.message_handler(commands=['setjoin'])
def handle_set_join(message: telebot.types.Message) -> None:
    """Handle command to set a group or channel that users must join to use the bot."""
    if is_admin_bot(message.from_user.id):
        try:
            _, group_or_channel_id = message.text.split()
            group_or_channel_id = int(group_or_channel_id)
            set_join_group_or_channel(group_or_channel_id)
            bot.reply_to(message, f"Group or channel with ID {group_or_channel_id} set as required for joining.")
        except ValueError:
            bot.reply_to(message, "Usage: /setjoin <group_or_channel_id>")
    else:
        bot.reply_to(message, "You do not have permission to use this command.")

@bot.message_handler(func=lambda message: not check_user_joined(message.from_user.id))
def handle_user_not_joined(message: telebot.types.Message) -> None:
    """Handle messages from users who have not joined the required group or channel."""
    join_requirements = get_join_requirements()
    if join_requirements:
        join_button = telebot.types.InlineKeyboardButton(text="Join Required Group/Channel", url=f"https://t.me/{join_requirements[0]}")
        keyboard = telebot.types.InlineKeyboardMarkup()
        keyboard.add(join_button)
        bot.reply_to(message, "You need to join the required group or channel before using this bot. Please join using the button below:", reply_markup=keyboard)
    else:
        bot.reply_to(message, "Access to this bot is restricted until you join the required group or channel.")

# Start polling
if __name__ == "__main__":
    bot.polling(none_stop=True)
