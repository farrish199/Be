import logging
import os
import telebot
import openai
from broadcast import (
    broadcast_to_user, broadcast_to_group, broadcast_to_channel, broadcast_to_all,
    schedule_user_broadcast, schedule_group_broadcast, schedule_channel_broadcast, schedule_all_broadcast
)
from handlers import (
    start, button, handle_message, set_admin_id, set_user_id, clone_bot,
    process_payment, payment_return, total_users, handle_downloader_fb,
    handle_downloader_tg, handle_downloader_ig, handle_downloader_tt,
    handle_downloader_yt
)
from keyboards import get_main_keyboard, get_submenu_keyboard, get_conversion_keyboard, SUBMENU_OPTIONS

# Set up logging
logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', level=logging.INFO)
logger = logging.getLogger(__name__)

# Get the bot token from environment variables
TOKEN = os.getenv('TELEGRAM_BOT_TOKEN')
if not TOKEN:
    logger.error("Telegram bot token is not set in environment variables.")
    exit(1)

# Set up OpenAI API key
OPENAI_API_KEY = os.getenv('OPENAI_API_KEY')
if not OPENAI_API_KEY:
    logger.error("OpenAI API key is not set in environment variables.")
    exit(1)
openai.api_key = OPENAI_API_KEY

# Create the bot instance
bot = telebot.TeleBot(TOKEN)

def save_auto_approve_group_id(group_id: int) -> None:
    """Save the group ID to a file."""
    with open('auto_approve_group_id.txt', 'w') as f:
        f.write(str(group_id))

def get_auto_approve_group_id() -> int:
    """Load the group ID from the file."""
    if os.path.exists('auto_approve_group_id.txt'):
        with open('auto_approve_group_id.txt', 'r') as f:
            return int(f.read().strip())
    return 0

@bot.message_handler(content_types=['new_chat_members'])
def handle_new_chat_member(message: telebot.types.Message) -> None:
    """Handle new members joining the group and automatically approve them."""
    if message.new_chat_members:
        for member in message.new_chat_members:
            if member.id == bot.get_me().id:
                group_id = message.chat.id
                save_auto_approve_group_id(group_id)
                bot.send_message(group_id, "Auto Approve is now enabled for this group.")
                break

    group_id = get_auto_approve_group_id()
    if group_id and message.chat.id == group_id:
        bot.approve_chat_join_request(message.chat.id, message.from_user.id)

@bot.message_handler(commands=['start'])
def handle_start(message: telebot.types.Message) -> None:
    """Handle the /start command and show the main menu."""
    markup = telebot.types.InlineKeyboardMarkup()
    button_service = telebot.types.InlineKeyboardButton(text='Service', callback_data='service')
    button_dev_bot = telebot.types.InlineKeyboardButton(text='Dev Bot', callback_data='dev_bot')
    button_support_bot = telebot.types.InlineKeyboardButton(text='Support Bot', callback_data='support_bot')
    button_clone_bot = telebot.types.InlineKeyboardButton(text='Clone Bot', callback_data='clone_bot')
    markup.add(button_service, button_dev_bot, button_support_bot, button_clone_bot)
    bot.send_message(message.chat.id, "Welcome! Please choose an option from the menu below:", reply_markup=markup)

def show_service_submenu(chat_id: int) -> None:
    """Show sub-menu options under 'Service'."""
    markup = telebot.types.InlineKeyboardMarkup()
    button_free_version = telebot.types.InlineKeyboardButton(text='Free Version', callback_data='free_version')
    button_premium_version = telebot.types.InlineKeyboardButton(text='Premium Version', callback_data='premium_version')
    markup.add(button_free_version, button_premium_version)
    bot.send_message(chat_id, "Please choose an option from the service below:", reply_markup=markup)

def show_version_submenu(chat_id: int, version_type: str) -> None:
    """Show sub-menu options under Free or Premium Version."""
    markup = telebot.types.InlineKeyboardMarkup()
    button_convert = telebot.types.InlineKeyboardButton(text='Convert', callback_data=f'{version_type}_convert')
    button_broadcast = telebot.types.InlineKeyboardButton(text='Broadcast', callback_data=f'{version_type}_broadcast')
    button_auto_approve = telebot.types.InlineKeyboardButton(text='Auto Approve', callback_data=f'{version_type}_auto_approve')
    button_downloader = telebot.types.InlineKeyboardButton(text='Downloader', callback_data=f'{version_type}_downloader')
    button_chatgpt = telebot.types.InlineKeyboardButton(text='ChatGPT', callback_data=f'{version_type}_chatgpt')
    markup.add(button_convert, button_broadcast, button_auto_approve, button_downloader, button_chatgpt)
    bot.send_message(chat_id, f"Please choose an option for {version_type}:", reply_markup=markup)

def show_downloader_submenu(chat_id: int, version_type: str) -> None:
    """Show sub-menu options under 'Downloader'."""
    markup = telebot.types.InlineKeyboardMarkup()
    button_fb = telebot.types.InlineKeyboardButton(text='FB', callback_data=f'{version_type}_fb')
    button_ig = telebot.types.InlineKeyboardButton(text='IG', callback_data=f'{version_type}_ig')
    button_tg = telebot.types.InlineKeyboardButton(text='TG', callback_data=f'{version_type}_tg')
    button_tt = telebot.types.InlineKeyboardButton(text='TT', callback_data=f'{version_type}_tt')
    button_yt = telebot.types.InlineKeyboardButton(text='YT', callback_data=f'{version_type}_yt')
    markup.add(button_fb, button_ig, button_tg, button_tt, button_yt)
    bot.send_message(chat_id, f"Please choose an option for {version_type} Downloader:", reply_markup=markup)

def show_convert_submenu(chat_id: int) -> None:
    """Show sub-menu options under 'Convert'."""
    markup = telebot.types.InlineKeyboardMarkup()
    button_bug_vless = telebot.types.InlineKeyboardButton(text='Bug Vless', callback_data='bug_vless')
    button_text_to_img = telebot.types.InlineKeyboardButton(text='Text to Img', callback_data='text_to_img')
    button_img_to_text = telebot.types.InlineKeyboardButton(text='Img to Text', callback_data='img_to_text')
    button_img_to_pdf = telebot.types.InlineKeyboardButton(text='Img to PDF', callback_data='img_to_pdf')
    button_pdf_to_img = telebot.types.InlineKeyboardButton(text='PDF to Img', callback_data='pdf_to_img')
    button_mp4_to_audio = telebot.types.InlineKeyboardButton(text='MP4 to Audio', callback_data='mp4_to_audio')
    markup.add(button_bug_vless, button_text_to_img, button_img_to_text, button_img_to_pdf, button_pdf_to_img, button_mp4_to_audio)
    bot.send_message(chat_id, f"Please choose an option for {version_type}:", reply_markup=markup)

def show_broadcast_submenu(chat_id: int) -> None:
    """Show sub-menu options under 'Broadcast'."""
    markup = telebot.types.InlineKeyboardMarkup()        
    button_broadcast_user = InlineKeyboardButton(text='Broadcast User', callback_data='broadcast_user')
    button_broadcast_group = InlineKeyboardButton(text='Broadcast Group', callback_data='broadcast_group')       
    button_broadcast_channel = InlineKeyboardButton(text='Broadcast Channel', callback_data='broadcast_channel')
    button_broadcast_all = InlineKeyboardButton(text='Broadcast All', callback_data='broadcast_all')
    button_schedule_user = InlineKeyboardButton(text='Schedule User', callback_data='schedule_user')
    button_schedule_group = InlineKeyboardButton(text='Schedule Group', callback_data='schedule_group')
    button_schedule_channel = InlineKeyboardButton(text='Schedule Channel', callback_data='schedule_channel')
    button_schedule_all = InlineKeyboardButton(text='Schedule All', callback_data='schedule_all')
    markup.add(button_broadcast_user, button_broadcast_group, button_broadcast_channel, button_broadcast_all, button_schedule_user, button_schedule_group,
    button_schedule_channel, button_schedule_all)
    bot.send_message(chat_id, f"Please choose an option for {version_type}:", reply_markup=markup)

def handle_chatgpt_query(user_query: str) -> str:
    """Send a query to OpenAI's ChatGPT API and return the response."""
    try:
        response = openai.Completion.create(
            model="text-davinci-003",
            prompt=user_query,
            max_tokens=150,
            temperature=0.7
        )
        return response.choices[0].text.strip()
    except Exception as e:
        logger.error(f"Error in ChatGPT API request: {e}")
        return "Sorry, I encountered an error while processing your request."

@bot.callback_query_handler(func=lambda call: call.data.startswith('service'))
def handle_service_callback(call: telebot.types.CallbackQuery) -> None:
    """Handle callback queries related to the 'Service' button."""
    if call.data == 'service':
        show_service_submenu(call.message.chat.id)

@bot.callback_query_handler(func=lambda call: call.data.startswith('free_version') or call.data.startswith('premium_version'))
def handle_version_callback(call: telebot.types.CallbackQuery) -> None:
    """Handle callback queries related to service versions."""
    version_type = call.data.split('_')[0]
    show_version_submenu(call.message.chat.id, version_type.capitalize())

@bot.callback_query_handler(func=lambda call: call.data.startswith(('free_version_downloader', 'premium_version_downloader')))
def handle_downloader_callback(call: telebot.types.CallbackQuery) -> None:
    """Handle callback queries for Downloader options."""
    version_type = call.data.split('_', 2)[0].capitalize()
    show_downloader_submenu(call.message.chat.id, version_type)

@bot.callback_query_handler(func=lambda call: call.data.startswith(('free_version_auto_approve', 'premium_version_auto_approve')))
def handle_auto_approve_callback(call: telebot.types.CallbackQuery) -> None:
    """Handle callback queries for Auto Approve options."""
    option = call.data.split('_', 2)[2]
    version_type = call.data.split('_', 1)[0].capitalize()
    bot.send_message(call.message.chat.id, f"Auto Approve functionality is now active for the {version_type} version.")
    group_id = get_auto_approve_group_id()
    if group_id:
        bot.send_message(call.message.chat.id, "Auto Approve feature is active. The bot will now monitor and approve group join requests.")

@bot.callback_query_handler(func=lambda call: call.data == 'clone_bot')
def handle_clone_bot_callback(call: telebot.types.CallbackQuery) -> None:
    """Handle callback queries related to the 'Clone Bot' button."""
    bot.send_message(call.message.chat.id, "To clone the bot, please use the /clone_bot command.")

@bot.callback_query_handler(func=lambda call: call.data == 'dev_bot')
def handle_dev_bot_callback(call: telebot.types.CallbackQuery) -> None:
    """Handle callback queries related to the 'Dev Bot' button."""
    bot.send_message(call.message.chat.id, "You can find more information about the bot at: https://t.me/abgomey")

@bot.callback_query_handler(func=lambda call: call.data == 'support_bot')
def handle_support_bot_callback(call: telebot.types.CallbackQuery) -> None:
    """Handle callback queries related to the 'Support Bot' button."""
    bot.send_message(call.message.chat.id, "For support, please contact us at: https://t.me/+X999yVVgz4I5NDdl")

@bot.callback_query_handler(func=lambda call: call.data.startswith(('free_version_chatgpt', 'premium_version_chatgpt')))
def handle_chatgpt_callback(call: telebot.types.CallbackQuery) -> None:
    """Handle callback queries related to the ChatGPT button."""
    version_type = call.data.split('_', 1)[0].capitalize()
    bot.send_message(call.message.chat.id, f"Please send me your query for {version_type} ChatGPT:")

@bot.message_handler(func=lambda message: message.text and message.text.startswith('Query:'))
def handle_chatgpt_message(message: telebot.types.Message) -> None:
    """Handle messages that should be sent to ChatGPT."""
    user_query = message.text[len('Query:'):].strip()
    response = handle_chatgpt_query(user_query)
    bot.send_message(message.chat.id, response)

@bot.callback_query_handler(func=lambda call: call.data.startswith('convert'))
def handle_convert_callback(call: telebot.types.CallbackQuery) -> None:
    """Handle callback queries related to 'Convert' button."""
    if call.data == 'convert':
        show_convert_submenu(call.message.chat.id)

@bot.callback_query_handler(func=lambda call: call.data.startswith('bug_vless'))
def handle_bug_vless_callback(call: telebot.types.CallbackQuery) -> None:
    bot.send_message(call.message.chat.id, "Bug Vless functionality is under development.")

@bot.callback_query_handler(func=lambda call: call.data.startswith('text_to_img'))
def handle_text_to_img_callback(call: telebot.types.CallbackQuery) -> None:
    bot.send_message(call.message.chat.id, "Text to Image functionality is under development.")

@bot.callback_query_handler(func=lambda call: call.data.startswith('img_to_text'))
def handle_img_to_text_callback(call: telebot.types.CallbackQuery) -> None:
    bot.send_message(call.message.chat.id, "Image to Text functionality is under development.")

@bot.callback_query_handler(func=lambda call: call.data.startswith('img_to_pdf'))
def handle_img_to_pdf_callback(call: telebot.types.CallbackQuery) -> None:
    bot.send_message(call.message.chat.id, "Image to PDF functionality is under development.")

@bot.callback_query_handler(func=lambda call: call.data.startswith('pdf_to_img'))
def handle_pdf_to_img_callback(call: telebot.types.CallbackQuery) -> None:
    bot.send_message(call.message.chat.id, "PDF to Image functionality is under development.")

@bot.callback_query_handler(func=lambda call: call.data.startswith('mp4_to_audio'))
def handle_mp4_to_audio_callback(call: telebot.types.CallbackQuery) -> None:
    bot.send_message(call.message.chat.id, "MP4 to Audio functionality is under development.")

@bot.message_handler(commands=['set_admin_id'])
def handle_set_admin_id(message: telebot.types.Message) -> None:
    set_admin_id(message, bot)

@bot.message_handler(commands=['set_user_id'])
def handle_set_user_id(message: telebot.types.Message) -> None:
    set_user_id(message, bot)

@bot.message_handler(commands=['process_payment'])
def handle_process_payment(message: telebot.types.Message) -> None:
    process_payment(message, bot)

@bot.message_handler(commands=['payment_return'])
def handle_payment_return(message: telebot.types.Message) -> None:
    payment_return(message, bot)

@bot.message_handler(commands=['total_users'])
def handle_total_users(message: telebot.types.Message) -> None:
    total_users(message, bot)

@bot.message_handler(commands=['downloader_fb'])
def downloader_fb(message: telebot.types.Message) -> None:
    handle_downloader_fb(message, bot)

@bot.message_handler(commands=['downloader_tg'])
def downloader_tg(message: telebot.types.Message) -> None:
    handle_downloader_tg(message, bot)

@bot.message_handler(commands=['downloader_ig'])
def downloader_ig(message: telebot.types.Message) -> None:
    handle_downloader_ig(message, bot)

@bot.message_handler(commands=['downloader_tt'])
def downloader_tt(message: telebot.types.Message) -> None:
    handle_downloader_tt(message, bot)

@bot.message_handler(commands=['downloader_yt'])
def downloader_yt(message: telebot.types.Message) -> None:
    handle_downloader_yt(message, bot)

@bot.message_handler(commands=['broadcast_user'])
def broadcast_to_user_command(message: telebot.types.Message) -> None:
    broadcast_to_user(message)

@bot.message_handler(commands=['broadcast_group'])
def broadcast_to_group_command(message: telebot.types.Message) -> None:
    broadcast_to_group(message)

@bot.message_handler(commands=['broadcast_channel'])
def broadcast_to_channel_command(message: telebot.types.Message) -> None:
    broadcast_to_channel(message)

@bot.message_handler(commands=['broadcast_all'])
def broadcast_to_all_command(message: telebot.types.Message) -> None:
    broadcast_to_all(message)

@bot.message_handler(commands=['schedule_user'])
def schedule_user_broadcast_command(message: telebot.types.Message) -> None:
    schedule_user_broadcast(message)

@bot.message_handler(commands=['schedule_group'])
def schedule_group_broadcast_command(message: telebot.types.Message) -> None:
    schedule_group_broadcast(message)

@bot.message_handler(commands=['schedule_channel'])
def schedule_channel_broadcast_command(message: telebot.types.Message) -> None:
    schedule_channel_broadcast(message)

@bot.message_handler(commands=['schedule_all'])
def schedule_all_broadcast_command(message: telebot.types.Message) -> None:
    schedule_all_broadcast(message)

@bot.message_handler(func=lambda message: not message.text.startswith('/'))
def handle_text_message(message: telebot.types.Message) -> None:
    handle_message(message, bot)

def main() -> None:
    try:
        logger.info("Starting bot...")
        bot.polling(none_stop=True)
    except Exception as e:
        logger.error(f"An error occurred: {e}")

if __name__ == '__main__':
    main()
