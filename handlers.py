import logging
import re
import json
import os
import random
import string
from datetime import datetime, timedelta
import requests
from pyrogram import Client, types
from config import ADMIN_USER_ID, ALLOWED_USER_IDS, PAID_USER_IDS, TOYYIBPAY_SECRET_KEY
from clonebot import get_user_data
from keyboards import get_main_keyboard, get_submenu_keyboard, get_conversion_keyboard, SUBMENU_OPTIONS

logger = logging.getLogger(__name__)

def is_user_allowed(user_id: int) -> bool:
    """Check if the user is allowed to use the bot."""
    return user_id == ADMIN_USER_ID or user_id in ALLOWED_USER_IDS

def is_user_paid(user_id: int) -> bool:
    """Check if the user has paid to access the bot."""
    user_data = load_user_data()
    return (user_id in user_data and
            user_data[user_id].get("subscription_end") and
            datetime.fromisoformat(user_data[user_id]["subscription_end"]) > datetime.now())

def load_user_data() -> dict:
    """Load user data from file."""
    if os.path.exists('user_data.json'):
        with open('user_data.json', 'r') as file:
            return json.load(file)
    return {}

def save_user_data(user_data: dict) -> None:
    """Save user data to file."""
    with open('user_data.json', 'w') as file:
        json.dump(user_data, file, indent=4)

def extract_info_from_text(user_text: str) -> tuple:
    """Extract UUID, subdomain, and name from a full vless URL."""
    pattern = r"vless://([^@]+)@([^:]+):(\d+)\?path=/vlessws&encryption=none&type=ws#(.+)"
    match = re.match(pattern, user_text)
    if match:
        uuid = match.group(1)
        subdo = match.group(2)
        name = match.group(4)
        return uuid, subdo, name
    return None, None, None

def handle_conversion(client: Client, message: types.Message) -> None:
    """Handle conversion options based on user's selected format."""
    user_text = message.text
    uuid, subdo, name = extract_info_from_text(user_text)
    if uuid and subdo and name:
        conversion_options = {
            "Digi BS": f"vless://{uuid}@162.159.134.61:80?path=/vlessws&encryption=none&type=ws&host={subdo}#{name}",
            "Digi XL": f"vless://{uuid}@app.optimizely.com:80?path=/vlessws&encryption=none&type=ws&host={subdo}#{name}",
            "UmoFunz XL": f"vless://{uuid}@your-address:80?path=/vlessws&encryption=none&type=ws&host=m.pubgmobile.com#{name}",
            "Maxis UL": f"vless://{uuid}@speedtest.net:443?path=/vlessws&encryption=none&type=ws&host=fast.{subdo}&sni=speedtest.net#{name}",
            "Unifi XL": f"vless://{uuid}@104.17.10.12:80?path=/vlessws&encryption=none&type=ws&host={subdo}#{name}",
            "Yes XL": f"vless://{uuid}@104.17.113.188:80?path=/vlessws&encryption=none&type=ws&host=tap-database.who.int.{subdo}#{name}",
            "Celcom XL": f"vless://{uuid}@104.17.148.22:80?path=/vlessws&encryption=none&type=ws&host=opensignal.com.{subdo}#{name}",
            "Booster 1": f"vless://{uuid}@104.17.147.22:80?path=/vlessws&encryption=none&type=ws&host={subdo}#{name}",
            "Booster 2": f"vless://{uuid}@www.speedtest.net:80?path=/vlessws&encryption=none&type=ws&host={subdo}#{name}"
        }
        reply = conversion_options.get(message.text, "Invalid option selected.")
        client.send_message(message.chat.id, reply)
    else:
        client.send_message(message.chat.id, "Invalid URL format. Please send a valid vless URL.")

def start(client: Client, message: types.Message) -> None:
    """Handle /start command."""
    client.send_message(
        message.chat.id,
        (
            "===================================\nBot MF By IMMANVPN\n\n"
            "Hi! Saya adalah bot yang dapat membantu anda dalam beberapa hal "
            "yang dapat memudahkan kerja anda!\n\nSaya mempunyai beberapa fungsi "
            "menarik yang dapat anda gunakan!\n\nJom Explore fungsi yang ada pada saya.\n"
            "==================================="
        ),
        reply_markup=get_main_keyboard()
    )

def button(client: Client, query: types.CallbackQuery) -> None:
    """Handle callback queries from inline buttons."""
    client.answer_callback_query(query.id)
    client.edit_message_text(f"Selected option: {query.data}", chat_id=query.message.chat.id, message_id=query.message.message_id)

def set_admin_id(client: Client, message: types.Message) -> None:
    """Set a new admin ID."""
    user_id = message.from_user.id
    if user_id == ADMIN_USER_ID:
        args = message.text.split()[1:]
        if len(args) != 1:
            client.send_message(message.chat.id, "Usage: /set_admin_id <new_admin_id>")
            return
        
        try:
            new_admin_id = int(args[0])
        except ValueError:
            client.send_message(message.chat.id, "Invalid admin ID format.")
            return

        update_config('ADMIN_USER_ID', str(new_admin_id))
        client.send_message(message.chat.id, "Admin ID has been updated.")
    else:
        client.send_message(message.chat.id, "You do not have permission to change the admin ID.")

def set_user_id(client: Client, message: types.Message) -> None:
    """Set new allowed user IDs."""
    user_id = message.from_user.id
    if user_id == ADMIN_USER_ID:
        args = message.text.split()[1:]
        if len(args) != 1:
            client.send_message(message.chat.id, "Usage: /set_user_id <user_ids_comma_separated>")
            return
        
        new_allowed_user_ids = args[0].split(',')
        update_config('ALLOWED_USER_IDS', ','.join(new_allowed_user_ids))
        client.send_message(message.chat.id, "Allowed user IDs have been updated.")
    else:
        client.send_message(message.chat.id, "You do not have permission to change the allowed user IDs.")

def clone_bot(client: Client, message: types.Message) -> None:
    """Clone the bot to another bot using the provided token."""
    user_id = message.from_user.id
    is_premium_user = is_user_paid(user_id)
    user_bot_limits = get_user_bot_limits()

    if is_premium_user:
        if user_bot_limits['premium_bots'] >= PREMIUM_VERSION_LIMIT:
            client.send_message(message.chat.id, "You have reached the maximum number of premium bots you can clone.")
            return
        user_bot_limits['premium_bots'] += 1
    else:
        if user_bot_limits['freemium_bots'] >= FREE_VERSION_LIMIT:
            client.send_message(message.chat.id, "You have reached the maximum number of freemium bots you can clone.")
            return
        user_bot_limits['freemium_bots'] += 1

    args = message.text.split()[1:]
    if len(args) != 1:
        client.send_message(message.chat.id, "Usage: /clone_bot <bot_token>")
        return
    
    bot_token = args[0]
    # Implement cloning logic here
    client.send_message(message.chat.id, f"Bot cloned successfully with token: {bot_token}")

def total_users(client: Client, message: types.Message) -> None:
    """Handle the /total_users command to show total number of users."""
    user_data_file = 'user_data.json'

    try:
        if os.path.exists(user_data_file):
            with open(user_data_file, 'r') as file:
                user_data = json.load(file)
                
            total_users_count = len(user_data)
            response_message = f"Total number of users: {total_users_count}"
        else:
            response_message = "User data file does not exist."
    except Exception as e:
        response_message = f"An error occurred: {e}"

    client.send_message(message.chat.id, response_message)

def handle_message(client: Client, message: types.Message) -> None:
    """Handle incoming text messages."""
    user_id = message.from_user.id
    if is_user_allowed(user_id):
        if message.text.startswith("vless://"):
            handle_conversion(client, message)
        elif message.text.startswith("/setprice"):
            # Implement the /setprice command here
            pass
        elif message.text.startswith("/toyyibapikey"):
            # Handle adding the ToyyibPay API key to the database
            pass
        else:
            client.send_message(message.chat.id, "Invalid message. Please send a valid vless URL or use the bot's commands.")
    else:
        client.send_message(message.chat.id, "You do not have permission to use this bot.")

def update_config(key: str, value: str) -> None:
    """Update configuration values."""
    config_file = 'config.py'
    with open(config_file, 'r') as file:
        config_content = file.read()
    
    new_content = re.sub(f'{key} = .+', f'{key} = {value}', config_content)
    
    with open(config_file, 'w') as file:
        file.write(new_content)

def get_user_bot_limits() -> dict:
    """Retrieve bot limits for the user."""
    return {
        'freemium_bots': 0,
        'premium_bots': 0
    }

FREE_VERSION_LIMIT = 1
PREMIUM_VERSION_LIMIT = 5
