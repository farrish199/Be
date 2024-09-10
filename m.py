import logging
import os
import json
import io
from pyrogram import Client, filters
from pyrogram.types import InlineKeyboardButton, InlineKeyboardMarkup, CallbackQuery
from convfunc import text_to_image, image_to_text, image_to_pdf, pdf_to_image
from mp423 import mp4_to_audio
from chatgpt import generate_chatgpt_response, extract_info_from_text
from admintf import (
    app as admin_bot, load_cloned_bots, load_admin_bot_id, is_admin_bot, save_json_file, schedule_broadcast_all, list_scheduled_jobs,
    cancel_scheduled_job, set_join_group_or_channel, get_join_requirements, check_user_joined, broadcast_to_all_bots, broadcast_to_freemium_bots,
    broadcast_to_premium_bots, list_admin_bot_ids, handle_schedule_user_broadcast, handle_schedule_group_broadcast, handle_schedule_channel_broadcast,
    handle_schedule_all_broadcast, handle_list_scheduled_jobs, handle_cancel_scheduled_job, handle_set_join, handle_user_not_joined
)
from broadcast import (
    load_json_file, load_user_data, load_group_ids, load_channel_ids, is_admin, is_freemium, is_premium, get_admins_of_chat, 
    schedule_broadcast, broadcast_to_user, broadcast_to_group, broadcast_to_channel, broadcast_to_all, schedule_user_broadcast,
    schedule_group_broadcast, schedule_channel_broadcast, schedule_all_broadcast
)
from handlers import (
    start, button, handle_message, set_admin_id, set_user_id, clone_bot, process_payment, payment_callback, total_users,
    handle_downloader_fb, handle_downloader_tg, handle_downloader_ig, handle_downloader_tt, handle_downloader_yt,
    is_user_allowed, is_user_paid, save_user_data, handle_conversion, generate_random_string, create_category, create_bill, update_config
)
from keyboards import get_main_keyboard, get_submenu_keyboard, get_conversion_keyboard, SUBMENU_OPTIONS
from config import TOKEN as TELEGRAM_BOT_TOKEN,API_ID, API_HASH, ADMIN_BOT_ID, ADMIN_USER_ID, ALLOWED_USER_IDS, PAID_USER_IDS, TOYYIBPAY_SECRET_KEY

# Setup logging
logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', level=logging.INFO)
logger = logging.getLogger(__name__)

API_ID = os.getenv("API_ID")
API_HASH = os.getenv("API_HASH")
BOT_TOKEN = os.getenv("BOT_TOKEN")

# Get the api id, api hash & telegram bot token from environment variables
app = Client("my_bot", api_id=API_ID, api_hash=API_HASH, bot_token=TELEGRAM_BOT_TOKEN)

def save_auto_approve_group_id(group_id: int) -> None:
    """Simpan ID kumpulan untuk kelulusan automatik."""
    try:
        with open('auto_approve_group_id.txt', 'w') as f:
            f.write(str(group_id))
    except Exception as e:
        logger.error(f"Ralat menyimpan ID kumpulan auto approve: {e}")

def get_auto_approve_group_id() -> int:
    """Muatkan ID kumpulan dari fail."""
    try:
        if os.path.exists('auto_approve_group_id.txt'):
            with open('auto_approve_group_id.txt', 'r') as f:
                return int(f.read().strip())
        return 0
    except Exception as e:
        logger.error(f"Ralat mendapatkan ID kumpulan auto approve: {e}")
        return 0

@app.on_message(filters.new_chat_members)
def handle_new_chat_member(client: Client, message: "Message") -> None:
    """Tangani ahli baru yang menyertai kumpulan dan luluskan mereka secara automatik."""
    try:
        if message.new_chat_members:
            for member in message.new_chat_members:
                if member.id == client.get_me().id:
                    group_id = message.chat.id
                    save_auto_approve_group_id(group_id)
                    client.send_message(group_id, "Auto Approve kini diaktifkan untuk kumpulan ini.")
                    break

        group_id = get_auto_approve_group_id()
        if group_id and message.chat.id == group_id:
            client.approve_chat_join_request(message.chat.id, message.from_user.id)
    except Exception as e:
        logger.error(f"Ralat mengendalikan ahli baru: {e}")

def save_user_data(user_id: int) -> None:
    """Simpan user_id ke dalam user_data.json."""
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
        logger.error(f"Ralat menyimpan data pengguna: {e}")

@app.on_message(filters.command("ask"))
def handle_ask_command(client: Client, message) -> None:
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
def handle_chatgpt_callback(client: Client, query: CallbackQuery) -> None:
    """Handle callback queries related to the ChatGPT button."""
    try:
        data = query.data
        chat_id = query.message.chat.id
        
        if data.startswith(('free_version_chatgpt', 'premium_version_chatgpt')):
            show_chatgpt_info(chat_id)
    except Exception as e:
        logger.error(f"Ralat mengendalikan callback: {e}")

def show_chatgpt_info(chat_id: int) -> None:
    """Hantar maklumat tentang cara menggunakan ChatGPT."""
    try:
        info_message = (
            "Untuk berinteraksi dengan ChatGPT, sila gunakan arahan /ask diikuti dengan soalan anda. "
            "Contohnya:\n\n"
            "/ask Apakah ibu kota Perancis?\n\n"
            "Bot akan menghantar soalan anda kepada ChatGPT dan memulangkan responsnya."
        )
        app.send_message(chat_id, info_message)
    except Exception as e:
        logger.error(f"Ralat memaparkan maklumat ChatGPT: {e}")

@app.on_message(filters.command('start'))
def handle_start(client: Client, message: "Message") -> None:
    """Tangani arahan /start dan tunjukkan menu utama."""
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
        client.send_message(message.chat.id, "Selamat datang! Sila pilih pilihan dari menu di bawah:", reply_markup=markup)
    except Exception as e:
        logger.error(f"Ralat mengendalikan arahan /start: {e}")

def show_service_submenu(chat_id: int) -> None:
    """Tunjukkan pilihan submenu di bawah 'Service'."""
    try:
        markup = InlineKeyboardMarkup()
        buttons = [
            InlineKeyboardButton(text='Free Version', callback_data='free_version'),
            InlineKeyboardButton(text='Premium Version', callback_data='premium_version')
        ]
        markup.add(*buttons)
        app.send_message(chat_id, "Sila pilih pilihan dari servis di bawah:", reply_markup=markup)
    except Exception as e:
        logger.error(f"Ralat memaparkan submenu servis: {e}")

def show_version_submenu(chat_id: int, version_type: str) -> None:
    """Tunjukkan pilihan submenu di bawah Versi Percuma atau Premium."""
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
        app.send_message(chat_id, f"Sila pilih pilihan untuk {version_type}:", reply_markup=markup)
    except Exception as e:
        logger.error(f"Ralat memaparkan submenu versi: {e}")

def show_downloader_submenu(chat_id: int, version_type: str) -> None:
    """Tunjukkan pilihan submenu di bawah 'Downloader'."""
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
        app.send_message(chat_id, f"Sila pilih pilihan Downloader untuk {version_type}:", reply_markup=markup)
    except Exception as e:
        logger.error(f"Ralat memaparkan submenu downloader: {e}")

def show_convert_submenu(chat_id: int) -> None:
    """Tunjukkan pilihan submenu di bawah 'Convert'."""
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
        app.send_message(chat_id, "Sila pilih pilihan Convert:", reply_markup=markup)
    except Exception as e:
        logger.error(f"Ralat memaparkan submenu convert: {e}")

def show_broadcast_submenu(chat_id: int) -> None:
    """Tunjukkan pilihan submenu di bawah 'Broadcast'."""
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
            InlineKeyboardButton(text='Schedule All', callback_data='schedule_all'),
            InlineKeyboardButton(text='List Scheduled Jobs', callback_data='list_scheduled_jobs')
        ]
        markup.add(*buttons)
        app.send_message(chat_id, "Sila pilih pilihan Broadcast:", reply_markup=markup)
    except Exception as e:
        logger.error(f"Ralat memaparkan submenu broadcast: {e}")

def show_chatgpt_submenu(chat_id: int) -> None:
    """Tunjukkan pilihan submenu di bawah 'ChatGPT'."""
    try:
        markup = InlineKeyboardMarkup()
        buttons = [
            InlineKeyboardButton(text='Generate Response', callback_data='generate_response'),
            InlineKeyboardButton(text='Extract Info', callback_data='extract_info')
        ]
        markup.add(*buttons)
        app.send_message(chat_id, "Sila pilih pilihan ChatGPT:", reply_markup=markup)
    except Exception as e:
        logger.error(f"Ralat memaparkan submenu ChatGPT: {e}")

@app.on_callback_query()
def handle_query(client: Client, query: CallbackQuery) -> None:
    """Tangani klik pada butang dalam menu."""
    try:
        data = query.data
        chat_id = query.message.chat.id
        
        if data == 'service':
            show_service_submenu(chat_id)
        elif data == 'free_version':
            show_version_submenu(chat_id, 'Free Version')
        elif data == 'premium_version':
            show_version_submenu(chat_id, 'Premium Version')
        elif data == 'free_convert':
            show_convert_submenu(chat_id)
        elif data == 'premium_convert':
            show_convert_submenu(chat_id)
        elif data == 'free_downloader':
            show_downloader_submenu(chat_id, 'Free Version')
        elif data == 'premium_downloader':
            show_downloader_submenu(chat_id, 'Premium Version')
        elif data == 'free_broadcast':
            show_broadcast_submenu(chat_id)
        elif data == 'premium_broadcast':
            show_broadcast_submenu(chat_id)
        elif data == 'free_chatgpt':
            show_chatgpt_submenu(chat_id)
        elif data == 'premium_chatgpt':
            show_chatgpt_submenu(chat_id)
        elif data.startswith('broadcast_user'):
            # Laksanakan siaran untuk pengguna
            pass
        elif data.startswith('broadcast_group'):
            # Laksanakan siaran untuk kumpulan
            pass
        elif data.startswith('broadcast_channel'):
            # Laksanakan siaran untuk saluran
            pass
        elif data.startswith('broadcast_all'):
            # Laksanakan siaran untuk semua
            pass
        elif data.startswith('schedule_user'):
            # Laksanakan penjadualan untuk pengguna
            pass
        elif data.startswith('schedule_group'):
            # Laksanakan penjadualan untuk kumpulan
            pass
        elif data.startswith('schedule_channel'):
            # Laksanakan penjadualan untuk saluran
            pass
        elif data.startswith('schedule_all'):
            # Laksanakan penjadualan untuk semua
            pass
        elif data == 'list_scheduled_jobs':
            # Paparkan senarai pekerjaan yang dijadualkan
            pass
        elif data.startswith('generate_response'):
            # Hasilkan respons ChatGPT
            pass
        elif data.startswith('extract_info'):
            # Ekstrak maklumat dari teks
            pass
        elif data.startswith('text_to_img'):
            # Tukar teks kepada imej
            pass
        elif data.startswith('img_to_text'):
            # Tukar imej kepada teks
            pass
        elif data.startswith('img_to_pdf'):
            # Tukar imej kepada PDF
            pass
        elif data.startswith('pdf_to_img'):
            # Tukar PDF kepada imej
            pass
        elif data.startswith('mp4_to_audio'):
            # Tukar MP4 kepada audio
            pass
        else:
            app.send_message(chat_id, "Pilihan tidak dikenali.")
    except Exception as e:
        logger.error(f"Ralat mengendalikan pertanyaan: {e}")

if __name__ == "__main__":
    app.run()
