import logging
import os
import json
from pyrogram import Client, filters
from pyrogram.types import InlineKeyboardButton, InlineKeyboardMarkup, CallbackQuery, Message
from chatgpt import generate_chatgpt_response, extract_info_from_text
from callurl import app
from payment import generate_random_string, create_category, create_bill, process_payment
from database import save_user_data, save_auto_approve_group_id, get_auto_approve_group_id
from limit import set_daily_limit, load_limits, save_limits, initialize_user, check_daily_limit, update_daily_usage

# Setup logging
logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', level=logging.INFO)
logger = logging.getLogger(__name__)

API_ID = os.getenv("API_ID")
API_HASH = os.getenv("API_HASH")
BOT_TOKEN = os.getenv("BOT_TOKEN")

# Initialize the Pyrogram Client
app = Client("my_bot", api_id=API_ID, api_hash=API_HASH, bot_token=BOT_TOKEN)

@app.on_message(filters.command('start'))
def handle_start(client: Client, message: Message) -> None:
    """Tangani arahan /start dan tunjukkan menu utama."""
    try:
        user_id = message.from_user.id
        save_user_data(user_id)
        initialize_user(user_id)  # Initialize limits for the new user
        
        # Text untuk mesej utama bot
        welcome_message = (
            "===================================\n"
            "Bot MF By IMMANVPN\n\n"
            "Hi! Saya adalah bot yang dapat membantu anda dalam beberapa hal yang dapat memudahkan kerja anda!\n\n"
            "Saya mempunyai beberapa fungsi menarik yang dapat anda gunakan!\n\n"
            "Jom Explore fungsi yang ada pada saya.\n"
            "==================================="
        )
        
        # Menyediakan markup dengan butang
        markup = InlineKeyboardMarkup(
            inline_keyboard=[
                [
                    InlineKeyboardButton(text='Service', callback_data='service')
                ],
                [
                    InlineKeyboardButton(text='Dev Bot', url='https://t.me/abgomey'),
                    InlineKeyboardButton(text='Support Bot', url='https://t.me/support_group')  # Gantikan dengan pautan kumpulan sokongan sebenar
                ]
            ]
        )
        client.send_message(message.chat.id, welcome_message, reply_markup=markup)
    except Exception as e:
        logger.error(f"Ralat mengendalikan arahan /start: {e}")

@app.on_message(filters.command("ask"))
def handle_ask_command(client: Client, message: Message) -> None:
    """Handle /ask command to interact with ChatGPT or extract information."""
    try:
        user_input = message.text[len('/ask'):].strip()
        if user_input.startswith('extract:'):
            text_to_extract = user_input[len('extract:'):].strip()
            extracted_info = extract_info_from_text(text_to_extract)
            client.send_message(message.chat.id, json.dumps(extracted_info, indent=2))
        else:
            response = generate_chatgpt_response(user_input)
            client.send_message(message.chat.id, response)
    except Exception as e:
        logger.error(f"Ralat mengendalikan arahan /ask: {e}")
        client.send_message(message.chat.id, "Maaf, terdapat ralat semasa memproses permintaan anda.")

@app.on_callback_query()
def handle_query(client: Client, query: CallbackQuery) -> None:
    """Tangani klik pada butang dalam menu."""
    try:
        data = query.data
        chat_id = query.message.chat.id
        
        if data == 'service':
            show_service_submenu(client, query.message)
        elif data == 'back_to_start':
            handle_start(client, query.message)
        elif data.endswith('_convert'):
            show_convert_submenu(chat_id, data.split('_')[0])
        elif data.endswith('_broadcast'):
            show_broadcast_submenu(chat_id, data.split('_')[0])
        elif data.endswith('_auto_approve'):
            show_auto_approve_submenu(chat_id, data.split('_')[0])
        elif data.endswith('_downloader'):
            show_downloader_submenu(chat_id, data.split('_')[0])
        elif data.endswith('_chatgpt'):
            show_chatgpt_submenu(chat_id, data.split('_')[0])
        elif data == 'back_to_version':
            show_version_submenu(chat_id, data.split('_')[0])
        else:
            client.send_message(chat_id, "Pilihan tidak dikenali.")
    except Exception as e:
        logger.error(f"Ralat mengendalikan pertanyaan: {e}")

@app.on_message(filters.command("service"))
def show_service_submenu(client: Client, message: Message) -> None:
    """Tunjukkan pilihan submenu di bawah 'Service'."""
    try:
        markup = InlineKeyboardMarkup(
            inline_keyboard=[
                [
                    InlineKeyboardButton(text='Free Version', callback_data='free_version'),
                    InlineKeyboardButton(text='Premium Version', callback_data='premium_version')
                ],
                [
                    InlineKeyboardButton(text='Back', callback_data='back_to_start')
                ]
            ]
        )
        client.send_message(message.chat.id, "Sila pilih versi:", reply_markup=markup)
    except Exception as e:
        logger.error(f"Ralat memaparkan submenu servis: {e}")

@app.on_callback_query(filters.regex(r'^(free_version|premium_version)$'))
def handle_version_selection(client: Client, callback_query: CallbackQuery) -> None:
    """Tanggapi pilihan versi dan tunjukkan submenu untuk versi yang dipilih."""
    try:
        version_type = callback_query.data
        show_version_submenu(client, callback_query.message.chat.id, version_type)
    except Exception as e:
        logger.error(f"Ralat memaparkan submenu versi: {e}")

def show_version_submenu(client: Client, chat_id: int, version_type: str) -> None:
    """Tunjukkan pilihan submenu di bawah Versi Free atau Premium."""
    try:
        markup = InlineKeyboardMarkup(
            inline_keyboard=[
                [
                    InlineKeyboardButton(text='Convert', callback_data=f'{version_type}_convert'),
                    InlineKeyboardButton(text='Broadcast', callback_data=f'{version_type}_broadcast'),
                    InlineKeyboardButton(text='Auto Approve', callback_data=f'{version_type}_auto_approve'),
                    InlineKeyboardButton(text='Downloader', callback_data=f'{version_type}_downloader'),
                    InlineKeyboardButton(text='ChatGPT', callback_data=f'{version_type}_chatgpt')
                ],
                [
                    InlineKeyboardButton(text='Back', callback_data='back_to_version')
                ]
            ]
        )
        client.send_message(chat_id, f"Sila pilih pilihan untuk {version_type}:", reply_markup=markup)
    except Exception as e:
        logger.error(f"Ralat memaparkan submenu versi: {e}")

@app.on_callback_query(filters.regex(r'^(free_version|premium_version)_(convert|broadcast|auto_approve|downloader|chatgpt|back_to_service)$'))
def handle_version_submenu(client: Client, callback_query: CallbackQuery) -> None:
    """Tanggapi pilihan submenu versi dan lakukan tindakan yang sesuai."""
    try:
        data = callback_query.data
        version_type, feature = data.split('_', 1)
        
        feature_function_map = {
            'convert': show_convert_submenu,
            'broadcast': show_broadcast_submenu,
            'auto_approve': show_auto_approve_submenu,
            'downloader': show_downloader_submenu,
            'chatgpt': show_chatgpt_submenu
        }
        
        feature_function_map.get(feature, lambda *args: None)(client, callback_query.message.chat.id, version_type)
        
        # Update usage for free version features
        if version_type == 'free_version':
            if not check_daily_limit(callback_query.from_user.id, feature, version_type):
                client.send_message(callback_query.message.chat.id, "Anda telah melebihi had harian untuk fungsi ini.")
                return
            update_daily_usage(callback_query.from_user.id, feature)
    except Exception as e:
        logger.error(f"Ralat memaparkan submenu versi: {e}")

def show_downloader_submenu(client: Client, chat_id: int, version_type: str) -> None:
    """Tunjukkan pilihan submenu di bawah 'Downloader'."""
    try:
        markup = InlineKeyboardMarkup(
            inline_keyboard=[
                [
                    InlineKeyboardButton(text='FB', callback_data=f'{version_type}_fb'),
                    InlineKeyboardButton(text='IG', callback_data=f'{version_type}_ig'),
                    InlineKeyboardButton(text='TG', callback_data=f'{version_type}_tg'),
                    InlineKeyboardButton(text='TT', callback_data=f'{version_type}_tt'),
                    InlineKeyboardButton(text='YT', callback_data=f'{version_type}_yt')
                ],
                [
                    InlineKeyboardButton(text='Back', callback_data=f'{version_type}_version')
                ]
            ]
        )
        client.send_message(chat_id, f"Sila pilih pilihan Downloader untuk {version_type}:", reply_markup=markup)
    except Exception as e:
        logger.error(f"Ralat memaparkan submenu downloader: {e}")

def show_convert_submenu(client: Client, chat_id: int, version_type: str) -> None:
    """Tunjukkan pilihan submenu di bawah 'Convert'."""
    try:
        markup = InlineKeyboardMarkup(
            inline_keyboard=[
                [
                    InlineKeyboardButton(text='Bug Vless', callback_data=f'{version_type}_bug_vless'),
                    InlineKeyboardButton(text='Text to Img', callback_data=f'{version_type}_text_to_img'),
                    InlineKeyboardButton(text='Img to Text', callback_data=f'{version_type}_img_to_text'),
                    InlineKeyboardButton(text='Img to PDF', callback_data=f'{version_type}_img_to_pdf'),
                    InlineKeyboardButton(text='PDF to Img', callback_data=f'{version_type}_pdf_to_img'),
                    InlineKeyboardButton(text='MP4 to Audio', callback_data=f'{version_type}_mp4_to_audio')
                ],
                [
                    InlineKeyboardButton(text='Back', callback_data=f'{version_type}_version')
                ]
            ]
        )
        client.send_message(chat_id, f"Sila pilih pilihan Convert {version_type}:", reply_markup=markup)
    except Exception as e:
        logger.error(f"Ralat memaparkan submenu convert: {e}")

def show_broadcast_submenu(client: Client, chat_id: int, version_type: str) -> None:
    """Tunjukkan pilihan submenu di bawah 'Broadcast'."""
    try:
        markup = InlineKeyboardMarkup(
            inline_keyboard=[
                [
                    InlineKeyboardButton(text='Broadcast User', callback_data=f'{version_type}_broadcast_user'),
                    InlineKeyboardButton(text='Broadcast Group', callback_data=f'{version_type}_broadcast_group'),
                    InlineKeyboardButton(text='Broadcast Channel', callback_data=f'{version_type}_broadcast_channel'),
                    InlineKeyboardButton(text='Broadcast All', callback_data=f'{version_type}_broadcast_all')
                ],
                [
                    InlineKeyboardButton(text='Schedule User', callback_data=f'{version_type}_schedule_user'),
                    InlineKeyboardButton(text='Schedule Group', callback_data=f'{version_type}_schedule_group'),
                    InlineKeyboardButton(text='Schedule Channel', callback_data=f'{version_type}_schedule_channel'),
                    InlineKeyboardButton(text='Schedule All', callback_data=f'{version_type}_schedule_all')
                ],
                [
                    InlineKeyboardButton(text='List Scheduled Jobs', callback_data=f'{version_type}_list_scheduled_jobs')
                ],
                [
                    InlineKeyboardButton(text='Back', callback_data=f'{version_type}_version')
                ]
            ]
        )
        client.send_message(chat_id, f"Sila pilih pilihan Broadcast {version_type}:", reply_markup=markup)
    except Exception as e:
        logger.error(f"Ralat memaparkan submenu broadcast: {e}")

def show_auto_approve_submenu(client: Client, chat_id: int, version_type: str) -> None:
    """Tunjukkan pilihan submenu di bawah 'Auto Approve' dengan hanya butang 'Back'."""
    try:
        markup = InlineKeyboardMarkup(
            inline_keyboard=[
                [
                    InlineKeyboardButton(text='Back', callback_data=f'{version_type}_version')
                ]
            ]
        )
        client.send_message(
            chat_id, 
            "Untuk mengaktifkan fungsi auto approve, tambahkan bot ke dalam group atau channel sebagai admin. \n\nKlik butang di bawah untuk kembali.", 
            reply_markup=markup
        )
    except Exception as e:
        logger.error(f"Ralat memaparkan submenu Auto Approve: {e}")

def show_chatgpt_submenu(client: Client, chat_id: int, version_type: str) -> None:
    """Tunjukkan pilihan submenu di bawah 'ChatGPT' dengan hanya butang 'Back'."""
    try:
        markup = InlineKeyboardMarkup(
            inline_keyboard=[
                [
                    InlineKeyboardButton(text='Back', callback_data=f'{version_type}_version')
                ]
            ]
        )
        client.send_message(
            chat_id, 
            "Sila gunakan arahan /ask untuk berinteraksi dengan ChatGPT. \n\nKlik butang di bawah untuk kembali.", 
            reply_markup=markup
        )
    except Exception as e:
        logger.error(f"Ralat memaparkan submenu ChatGPT: {e}")

if __name__ == "__main__":
    app.run()
