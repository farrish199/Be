import logging
import re
import telebot
import json
import os
from datetime import datetime, timedelta
import requests
from config import ADMIN_USER_ID, ALLOWED_USER_IDS, PAID_USER_IDS, TOYYIBPAY_API_KEY, TOYYIBPAY_MERCHANT_CODE, TOYYIBPAY_SECRET_KEY
from clone_bot import get_user_data
from keyboards import get_main_keyboard, get_submenu_keyboard, SUBMENU_OPTIONS

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
    """Extract UUID, subdo, and name from a full vless URL."""
    pattern = r"vless://([^@]+)@([^:]+):(\d+)\?path=/vlessws&encryption=none&type=ws#(.+)"
    match = re.match(pattern, user_text)
    if match:
        uuid = match.group(1)
        subdo = match.group(2)
        name = match.group(4)
        return uuid, subdo, name
    return None, None, None

def handle_conversion(message: telebot.types.Message, bot: telebot.TeleBot) -> None:
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
        bot.reply_to(message, reply)
    else:
        bot.reply_to(message, "Invalid URL format. Please send a valid vless URL.")

def start(message: telebot.types.Message, bot: telebot.TeleBot) -> None:
    """Handle /start command."""
    bot.reply_to(message, (
        "===================================\nBot MF By IMMANVPN\n\n"
        "Hi! Saya adalah bot yang dapat membantu anda dalam beberapa hal "
        "yang dapat memudahkan kerja anda!\n\nSaya mempunyai beberapa fungsi "
        "menarik yang dapat anda gunakan!\n\nJom Explore fungsi yang ada pada saya.\n"
        "==================================="),
        reply_markup=get_main_keyboard()
    )

def button(call: telebot.types.CallbackQuery, bot: telebot.TeleBot) -> None:
    """Handle callback queries from inline buttons."""
    bot.answer_callback_query(call.id)
    bot.edit_message_text(f"Selected option: {call.data}", chat_id=call.message.chat.id, message_id=call.message.message_id)

def handle_message(message: telebot.types.Message, bot: telebot.TeleBot) -> None:
    """Handle incoming text messages."""
    user_id = message.from_user.id
    if is_user_allowed(user_id):
        if message.text.startswith("vless://"):
            handle_conversion(message, bot)
        else:
            bot.reply_to(message, "Invalid message. Please send a valid vless URL or use the bot's commands.")
    else:
        bot.reply_to(message, "You do not have permission to use this bot.")

def set_admin_id(message: telebot.types.Message, bot: telebot.TeleBot) -> None:
    """Set a new admin ID."""
    user_id = message.from_user.id
    if user_id == ADMIN_USER_ID:
        args = message.text.split()[1:]
        if len(args) != 1:
            bot.reply_to(message, "Usage: /set_admin_id <new_admin_id>")
            return
        
        try:
            new_admin_id = int(args[0])
        except ValueError:
            bot.reply_to(message, "Invalid admin ID format.")
            return

        update_config('ADMIN_USER_ID', str(new_admin_id))
        bot.reply_to(message, "Admin ID has been updated.")
    else:
        bot.reply_to(message, "You do not have permission to change the admin ID.")

def set_user_id(message: telebot.types.Message, bot: telebot.TeleBot) -> None:
    """Set new allowed user IDs."""
    user_id = message.from_user.id
    if user_id == ADMIN_USER_ID:
        args = message.text.split()[1:]
        if len(args) != 1:
            bot.reply_to(message, "Usage: /set_user_id <user_ids_comma_separated>")
            return
        
        new_allowed_user_ids = args[0].split(',')
        update_config('ALLOWED_USER_IDS', ','.join(new_allowed_user_ids))
        bot.reply_to(message, "Allowed user IDs have been updated.")
    else:
        bot.reply_to(message, "You do not have permission to change the allowed user IDs.")

def clone_bot(message: telebot.types.Message, bot: telebot.TeleBot) -> None:
    """Clone the bot to another bot using the provided token."""
    user_id = message.from_user.id
    is_premium_user = is_user_paid(user_id)
    user_bot_limits = get_user_bot_limits()

    if is_premium_user:
        if user_bot_limits['premium_bots'] >= PREMIUM_VERSION_LIMIT:
            bot.reply_to(message, "You have reached the maximum number of premium bots you can clone.")
            return
        user_bot_limits['premium_bots'] += 1
    else:
        if user_bot_limits['freemium_bots'] >= FREE_VERSION_LIMIT:
            bot.reply_to(message, "You have reached the maximum number of freemium bots you can clone.")
            return
        user_bot_limits['freemium_bots'] += 1

    args = message.text.split()[1:]
    if len(args) != 1:
        bot.reply_to(message, "Usage: /clone_bot <bot_token>")
        return
    
    bot_token = args[0]
    # Implement cloning logic here
    bot.reply_to(message, f"Bot cloned successfully with token: {bot_token}")

def process_payment(message: telebot.types.Message, bot: telebot.TeleBot) -> None:
    """Create a payment invoice and send the payment link to the user."""
    user_id = message.from_user.id
    payment_url = "https://toyyibpay.com/index.php/api/create_invoice"
    payload = {
        "api_key": TOYYIBPAY_API_KEY,
        "merchant_code": TOYYIBPAY_MERCHANT_CODE,
        "secret_key": TOYYIBPAY_SECRET_KEY,
        "invoice_no": f"INV-{user_id}",
        "amount": 5.00,  # Amount to be paid
        "description": "Access to Bot for 30 days",
        "return_url": "https://yourdomain.com/payment_return"  # Update with your actual return URL
    }
    
    try:
        response = requests.post(payment_url, json=payload)
        response.raise_for_status()
        data = response.json()

        if data.get('status') == 'success':
            payment_link = data.get('payment_url')
            bot.reply_to(message, f"Please complete your payment by visiting: {payment_link}")
        else:
            bot.reply_to(message, "Failed to create payment link. Please try again later.")
    except requests.RequestException as e:
        logger.error(f"Payment request failed: {e}")
        bot.reply_to(message, "An error occurred while processing the payment. Please try again later.")

def payment_return(message: telebot.types.Message, bot: telebot.TeleBot) -> None:
    """Handle payment return and update user status."""
    try:
        data = message.text.split()
        if len(data) < 2:
            bot.reply_to(message, "Invalid payment data.")
            return
        
        user_id = int(data[0])
        status = data[1]
        
        if status == "success":
            user_data = load_user_data()
            subscription_end = datetime.now() + timedelta(days=30)
            user_data[user_id] = {"subscription_end": subscription_end.isoformat()}
            save_user_data(user_data)
            bot.reply_to(message, "Payment successful! You now have access to premium features.")
        else:
            bot.reply_to(message, "Payment failed. Please try again.")
    except ValueError:
        bot.reply_to(message, "Invalid payment data format.")
    except Exception as e:
        logger.error(f"Payment return handling failed: {e}")
        bot.reply_to(message, "An error occurred while processing the payment return.")

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
