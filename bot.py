import logging
import os
import json
import io
import telebot
from telebot.types import InlineKeyboardButton, InlineKeyboardMarkup
from convfunc import text_to_image, image_to_text, image_to_pdf, pdf_to_image
from mp423 import mp4_to_audio
from chatgpt import generate_chatgpt_response, extract_info_from_text
from admintf import (
    bot as admin_bot, load_cloned_bots, load_admin_bot_id, is_admin_bot, 
    save_json_file, schedule_broadcast_all, list_scheduled_jobs, cancel_scheduled_job,
    set_join_group_or_channel, get_join_requirements, check_user_joined, 
    broadcast_to_all_bots, broadcast_to_freemium_bots, broadcast_to_premium_bots,
    list_admin_bot_ids, handle_schedule_user_broadcast, handle_schedule_group_broadcast,
    handle_schedule_channel_broadcast, handle_schedule_all_broadcast, handle_list_scheduled_jobs,
    handle_cancel_scheduled_job, handle_set_join, handle_user_not_joined
)
from broadcast import (
    load_json_file, load_user_data, load_group_ids, load_channel_ids, 
    is_admin, is_freemium, is_premium, get_admins_of_chat, schedule_broadcast, 
    broadcast_to_user, broadcast_to_group, broadcast_to_channel, broadcast_to_all, 
    schedule_user_broadcast, schedule_group_broadcast, schedule_channel_broadcast, 
    schedule_all_broadcast
)
from handlers import (
    start, button, handle_message, set_admin_id, set_user_id, clone_bot, 
    process_payment, payment_callback, total_users, handle_downloader_fb, 
    handle_downloader_tg, handle_downloader_ig, handle_downloader_tt, 
    handle_downloader_yt, is_user_allowed, is_user_paid, save_user_data, 
    handle_conversion, generate_random_string, create_category, create_bill, update_config
)
from keyboards import get_main_keyboard, get_submenu_keyboard, get_conversion_keyboard
from config import (
    TOKEN as TELEGRAM_BOT_TOKEN, ADMIN_BOT_ID, ADMIN_USER_ID, 
    ALLOWED_USER_IDS, PAID_USER_IDS, TOYYIBPAY_SECRET_KEY
)

# Setup logging
logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', level=logging.INFO)
logger = logging.getLogger(__name__)

# Get the bot token from environment variables
TOKEN = os.getenv('TELEGRAM_BOT_TOKEN', TELEGRAM_BOT_TOKEN)
if not TOKEN:
    logger.error("Telegram bot token is not set.")
    exit(1)

# Create the bot instance
bot = telebot.TeleBot(TOKEN)

def save_auto_approve_group_id(group_id: int) -> None:
    """Save the group ID to a file."""
    try:
        with open('auto_approve_group_id.txt', 'w') as f:
            f.write(str(group_id))
    except Exception as e:
        logger.error(f"Error saving auto approve group ID: {e}")

def get_auto_approve_group_id() -> int:
    """Load the group ID from the file."""
    try:
        if os.path.exists('auto_approve_group_id.txt'):
            with open('auto_approve_group_id.txt', 'r') as f:
                return int(f.read().strip())
        return 0
    except Exception as e:
        logger.error(f"Error getting auto approve group ID: {e}")
        return 0

@bot.message_handler(content_types=['new_chat_members'])
def handle_new_chat_member(message: telebot.types.Message) -> None:
    """Handle new members joining the group and automatically approve them."""
    try:
        if message.new_chat_members:
            for member in message.new_chat_members:
                if member.id == bot.get_me().id:
                    group_id = message.chat.id
                    save_auto_approve_group_id(group_id)
                    bot.send_message(group_id, "Auto Approve is now enabled for this group.")
                    break

        if message.chat.id == get_auto_approve_group_id():
            bot.approve_chat_join_request(message.chat.id, message.from_user.id)
    except Exception as e:
        logger.error(f"Error handling new chat member: {e}")

def save_user_data(user_id: int) -> None:
    """Save user_id to user_data.json."""
    try:
        file_path = 'user_data.json'
        data = {}
        if os.path.exists(file_path):
            with open(file_path, 'r') as f:
                data = json.load(f)

        data[str(user_id)] = {"user_id": user_id}

        with open(file_path, 'w') as f:
            json.dump(data, f, indent=4)
    except Exception as e:
        logger.error(f"Error saving user data: {e}")

@bot.message_handler(commands=['start'])
def handle_start(message: telebot.types.Message) -> None:
    """Handle the /start command and show the main menu."""
    try:
        user_id = message.from_user.id
        save_user_data(user_id)
        
        markup = InlineKeyboardMarkup()
        buttons = [
            InlineKeyboardButton(text='Service', callback_data='service'),
            InlineKeyboardButton(text='Dev Bot', callback_data='dev_bot'),
            InlineKeyboardButton(text='Support Bot', callback_data='support_bot'),
            InlineKeyboardButton(text='Clone Bot', callback_data='clone_bot')
        ]
        markup.add(*buttons)
        bot.send_message(message.chat.id, "Welcome! Please choose an option from the menu below:", reply_markup=markup)
    except Exception as e:
        logger.error(f"Error handling /start command: {e}")

def show_service_submenu(chat_id: int) -> None:
    """Show sub-menu options under 'Service'."""
    try:
        markup = InlineKeyboardMarkup()
        buttons = [
            InlineKeyboardButton(text='Free Version', callback_data='free_version'),
            InlineKeyboardButton(text='Premium Version', callback_data='premium_version')
        ]
        markup.add(*buttons)
        bot.send_message(chat_id, "Please choose an option from the service below:", reply_markup=markup)
    except Exception as e:
        logger.error(f"Error showing service submenu: {e}")

def show_version_submenu(chat_id: int, version_type: str) -> None:
    """Show sub-menu options under Free or Premium Version."""
    try:
        markup = InlineKeyboardMarkup()
        buttons = [
            InlineKeyboardButton(text='Convert', callback_data=f'{version_type}_convert'),
            InlineKeyboardButton(text='Broadcast', callback_data=f'{version_type}_broadcast'),
            InlineKeyboardButton(text='Auto Approve', callback_data=f'{version_type}_auto_approve'),
            InlineKeyboardButton(text='Downloader', callback_data=f'{version_type}_downloader'),
            InlineKeyboardButton(text='ChatGPT', callback_data=f'{version_type}_chatgpt')
        ]
        markup.add(*buttons)
        bot.send_message(chat_id, f"Please choose an option for {version_type}:", reply_markup=markup)
    except Exception as e:
        logger.error(f"Error showing version submenu: {e}")

def show_downloader_submenu(chat_id: int, version_type: str) -> None:
    """Show sub-menu options under 'Downloader'."""
    try:
        markup = InlineKeyboardMarkup()
        buttons = [
            InlineKeyboardButton(text='FB', callback_data=f'{version_type}_fb'),
            InlineKeyboardButton(text='IG', callback_data=f'{version_type}_ig'),
            InlineKeyboardButton(text='TG', callback_data=f'{version_type}_tg'),
            InlineKeyboardButton(text='TT', callback_data=f'{version_type}_tt'),
            InlineKeyboardButton(text='YT', callback_data=f'{version_type}_yt')
        ]
        markup.add(*buttons)
        bot.send_message(chat_id, f"Please choose an option for {version_type} Downloader:", reply_markup=markup)
    except Exception as e:
        logger.error(f"Error showing downloader submenu: {e}")

def show_convert_submenu(chat_id: int) -> None:
    """Show sub-menu options under 'Convert'."""
    try:
        markup = InlineKeyboardMarkup()
        buttons = [
            InlineKeyboardButton(text='Bug Vless', callback_data='bug_vless'),
            InlineKeyboardButton(text='Text to Img', callback_data='text_to_img'),
            InlineKeyboardButton(text='Img to Text', callback_data='img_to_text'),
            InlineKeyboardButton(text='Img to PDF', callback_data='img_to_pdf'),
            InlineKeyboardButton(text='PDF to Img', callback_data='pdf_to_img'),
            InlineKeyboardButton(text='MP4 to Audio', callback_data='mp4_to_audio')
        ]
        markup.add(*buttons)
        bot.send_message(chat_id, "Please choose an option for Convert:", reply_markup=markup)
    except Exception as e:
        logger.error(f"Error showing convert submenu: {e}")

def show_broadcast_submenu(chat_id: int) -> None:
    """Show sub-menu options under 'Broadcast'."""
    try:
        markup = InlineKeyboardMarkup()
        buttons = [
            InlineKeyboardButton(text='Broadcast User', callback_data='broadcast_user'),
            InlineKeyboardButton(text='Broadcast Group', callback_data='broadcast_group'),
            InlineKeyboardButton(text='Broadcast Channel', callback_data='broadcast_channel'),
            InlineKeyboardButton(text='Broadcast All', callback_data='broadcast_all'),
            InlineKeyboardButton(text='Schedule User', callback_data='schedule_user'),
            InlineKeyboardButton(text='Schedule Group', callback_data='schedule_group'),
            InlineKeyboardButton(text='Schedule Channel', callback_data='schedule_channel'),
            InlineKeyboardButton(text='Schedule All', callback_data='schedule_all')
        ]
        markup.add(*buttons)
        bot.send_message(chat_id, "Please choose an option for Broadcast:", reply_markup=markup)
    except Exception as e:
        logger.error(f"Error showing broadcast submenu: {e}")

def show_auto_approve_submenu(chat_id: int) -> None:
    """Show sub-menu options under 'Auto Approve'."""
    try:
        markup = InlineKeyboardMarkup()
        buttons = [
            InlineKeyboardButton(text='Enable Auto Approve', callback_data='enable_auto_approve'),
            InlineKeyboardButton(text='Disable Auto Approve', callback_data='disable_auto_approve')
        ]
        markup.add(*buttons)
        bot.send_message(chat_id, "Please choose an option for Auto Approve:", reply_markup=markup)
    except Exception as e:
        logger.error(f"Error showing auto approve submenu: {e}")

@bot.callback_query_handler(func=lambda call: True)
def handle_callback_query(call: telebot.types.CallbackQuery) -> None:
    """Handle callback queries."""
    try:
        data = call.data
        chat_id = call.message.chat.id

        if data == 'service':
            show_service_submenu(chat_id)
        elif data in ['free_version', 'premium_version']:
            show_version_submenu(chat_id, data)
        elif data in ['free_version_convert', 'premium_version_convert']:
            show_convert_submenu(chat_id)
        elif data in ['free_version_broadcast', 'premium_version_broadcast']:
            show_broadcast_submenu(chat_id)
        elif data in ['free_version_auto_approve', 'premium_version_auto_approve']:
            show_auto_approve_submenu(chat_id)
        elif data in ['free_version_fb', 'premium_version_fb', 'free_version_ig', 'premium_version_ig',
                      'free_version_tg', 'premium_version_tg', 'free_version_tt', 'premium_version_tt',
                      'free_version_yt', 'premium_version_yt']:
            # Handle downloader options
            show_downloader_submenu(chat_id, data.split('_')[0] + '_' + data.split('_')[1])
        else:
            bot.send_message(chat_id, "Unknown option selected.")
    except Exception as e:
        logger.error(f"Error handling callback query: {e}")

# Run the bot
if __name__ == "__main__":
    try:
        bot.polling(none_stop=True)
    except Exception as e:
        logger.error(f"Error running bot: {e}")
