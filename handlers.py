import logging
import re
import telebot
import json
import os
import random
import string
from datetime import datetime, timedelta
import requests
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

def total_users(message):
    """Handle the /total_users command to show total number of users."""
    # Path to the file where user data is stored
    user_data_file = 'user_data.json'

    try:
        # Load user data
        if os.path.exists(user_data_file):
            with open(user_data_file, 'r') as file:
                user_data = json.load(file)
                
            # Calculate the number of users
            total_users_count = len(user_data)
            response_message = f"Total number of users: {total_users_count}"
        else:
            response_message = "User data file does not exist."
    except Exception as e:
        response_message = f"An error occurred: {e}"

    # Send response message back to the chat
    # Assuming `bot` is the TeleBot instance that is globally accessible
    bot.send_message(message.chat.id, response_message)

def generate_random_string(length=8) -> str:
    """Generate a random string of fixed length."""
    letters = string.ascii_letters + string.digits
    return ''.join(random.choice(letters) for i in range(length))

def create_category() -> str:
    """Create a category in ToyyibPay and return the category code."""
    category_name = f"Telegram Payment for {generate_random_string()}"
    category_description = "Payment for bot services"
    
    payload = {
        'catname': category_name,
        'catdescription': category_description,
        'userSecretKey': TOYYIBPAY_SECRET_KEY
    }
    
    try:
        response = requests.post('https://toyyibpay.com/index.php/api/createCategory', data=payload)
        response.raise_for_status()
        data = response.json()
        return data[0]['CategoryCode']
    except requests.RequestException as e:
        logger.error(f"Category creation failed: {e}")
        return None

def create_bill(category_code: str, user_id: int, price_code: int, item_name: str) -> str:
    """Create a bill in ToyyibPay and return the payment URL."""
    bill_amount = price_code
    bill_name = generate_random_string(10)
    bill_description = f"Bill for {user_id}"
    order_id = f"{user_id}_{bill_name}_{item_name}"
    
    payload = {
        'userSecretKey': TOYYIBPAY_SECRET_KEY,
        'categoryCode': category_code,
        'billName': bill_name,
        'billDescription': bill_description,
        'billPriceSetting': 1,
        'billPayorInfo': 1,
        'billAmount': bill_amount,
        'billReturnUrl': 'https://yourdomain.com/payment_return',
        'billCallbackUrl': 'https://yourdomain.com/payment_callback',
        'billExternalReferenceNo': order_id,
        'billTo': '',
        'billEmail': '',  # Add user email if needed
        'billPhone': '',  # Add user phone number if needed
        'billSplitPayment': 0,
        'billPaymentChannel': '0',
        'billContentEmail': 'Thank you for purchasing!',
        'billChargeToCustomer': 1,
        'billExpiryDays': 1
    }
    
    try:
        response = requests.post('https://toyyibpay.com/index.php/api/createBill', data=payload)
        response.raise_for_status()
        data = response.json()
        bill_code = data[0]['BillCode']
        return f"https://toyyibpay.com/{bill_code}"
    except requests.RequestException as e:
        logger.error(f"Bill creation failed: {e}")
        return None

def process_payment(message: telebot.types.Message, bot: telebot.TeleBot) -> None:
    """Create a payment invoice and send the payment link to the user."""
    user_id = message.from_user.id
    
    category_code = create_category()
    if not category_code:
        bot.reply_to(message, "Failed to create payment category. Please try again later.")
        return
    
    price_code = 500  # Example: RM5
    item_name = "premium_access"
    
    payment_url = create_bill(category_code, user_id, price_code, item_name)
    if payment_url:
        bot.reply_to(message, f"Please complete your payment by visiting: {payment_url}")
    else:
        bot.reply_to(message, "Failed to create payment link. Please try again later.")

def payment_callback(request: requests.Request) -> None:
    """Handle payment callback and update user status."""
    try:
        data = request.json()
        bill_code = data.get('billcode')
        status = data.get('status')
        user_id = int(data.get('order_id').split('_')[0])
        
        if status == '1':  # Success
            user_data = load_user_data()
            subscription_end = datetime.now() + timedelta(days=30)
            user_data[user_id] = {"subscription_end": subscription_end.isoformat()}
            save_user_data(user_data)
            # Notify user
            bot.send_message(user_id, "Payment successful! You now have access to premium features.")
        else:
            bot.send_message(user_id, "Payment failed. Please try again.")
    except Exception as e:
        logger.error(f"Payment callback handling failed: {e}")

def handle_message(message: telebot.types.Message, bot: telebot.TeleBot) -> None:
    """Handle incoming text messages."""
    user_id = message.from_user.id
    if is_user_allowed(user_id):
        if message.text.startswith("vless://"):
            handle_conversion(message, bot)
        elif message.text.startswith("/setprice"):
            # Implement the /setprice command here
            pass
        elif message.text.startswith("/toyyibapikey"):
            # Handle adding the ToyyibPay API key to the database
            pass
        else:
            bot.reply_to(message, "Invalid message. Please send a valid vless URL or use the bot's commands.")
    else:
        bot.reply_to(message, "You do not have permission to use this bot.")

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
