import logging
import os
import json
from pyrogram import Client, filters
from pyrogram.types import InlineKeyboardButton, InlineKeyboardMarkup, CallbackQuery, Message

# Setup logging
logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', level=logging.INFO)
logger = logging.getLogger(__name__)

API_ID = os.getenv("API_ID")
API_HASH = os.getenv("API_HASH")
BOT_TOKEN = os.getenv("BOT_TOKEN")

# Initialize the Pyrogram Client
app = Client("my_bot", api_id=API_ID, api_hash=API_HASH, bot_token=BOT_TOKEN)

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
def handle_new_chat_member(client: Client, message: Message) -> None:
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

@app.on_message(filters.command('start'))
def handle_start(client: Client, message: Message) -> None:
    """Tangani arahan /start dan tunjukkan menu utama."""
    try:
        user_id = message.from_user.id
        save_user_data(user_id)
        
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
                    InlineKeyboardButton(text='Service', callback_data='service'),
                    InlineKeyboardButton(text='Dev Bot', url='https://t.me/abgomey')
                ],
                [
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
            show_service_submenu(chat_id)
        elif data.endswith('_convert'):
            show_convert_submenu(chat_id)
        elif data.endswith('_broadcast'):
            show_broadcast_submenu(chat_id)
        elif data.endswith('_auto_approve'):
            # This is to be handled separately, no submenu
            pass
        elif data.endswith('_downloader'):
            show_downloader_submenu(chat_id, data.split('_')[0])
        elif data.endswith('_chatgpt'):
            show_chatgpt_submenu(chat_id)
        elif data == 'auto_approve':
            group_id = get_auto_approve_group_id()
            if group_id:
                client.send_message(chat_id, f"Auto Approve diaktifkan untuk kumpulan ID {group_id}.")
            else:
                client.send_message(chat_id, "Tiada kumpulan auto approve yang disimpan.")
        else:
            client.send_message(chat_id, "Pilihan tidak dikenali.")
    except Exception as e:
        logger.error(f"Ralat mengendalikan pertanyaan: {e}")

def show_service_submenu(chat_id: int) -> None:
    """Tunjukkan pilihan submenu di bawah 'Service'."""
    try:
        markup = InlineKeyboardMarkup(
            inline_keyboard=[
                [
                    InlineKeyboardButton(text='Free Version', callback_data='free_version'),
                    InlineKeyboardButton(text='Premium Version', callback_data='premium_version')
                ]
            ]
        )
        app.send_message(chat_id, "Sila pilih versi:", reply_markup=markup)
    except Exception as e:
        logger.error(f"Ralat memaparkan submenu servis: {e}")

def show_version_submenu(chat_id: int, version_type: str) -> None:
    """Tunjukkan pilihan submenu di bawah Versi Percuma atau Premium."""
    try:
        markup = InlineKeyboardMarkup(
            inline_keyboard=[
                [
                    InlineKeyboardButton(text='Convert', callback_data=f'{version_type}_convert'),
                    InlineKeyboardButton(text='Broadcast', callback_data=f'{version_type}_broadcast'),
                    InlineKeyboardButton(text='Auto Approve', callback_data=f'{version_type}_auto_approve'),
                    InlineKeyboardButton(text='Downloader', callback_data=f'{version_type}_downloader'),
                    InlineKeyboardButton(text='ChatGPT', callback_data=f'{version_type}_chatgpt')
                ]
            ]
        )
        app.send_message(chat_id, f"Sila pilih pilihan untuk {version_type}:", reply_markup=markup)
    except Exception as e:
        logger.error(f"Ralat memaparkan submenu versi: {e}")

def show_downloader_submenu(chat_id: int, version_type: str) -> None:
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
                ]
            ]
        )
        app.send_message(chat_id, f"Sila pilih pilihan Downloader untuk {version_type}:", reply_markup=markup)
    except Exception as e:
        logger.error(f"Ralat memaparkan submenu downloader: {e}")

def show_convert_submenu(chat_id: int) -> None:
    """Tunjukkan pilihan submenu di bawah 'Convert'."""
    try:
        markup = InlineKeyboardMarkup(
            inline_keyboard=[
                [
                    InlineKeyboardButton(text='Bug Vless', callback_data='bug_vless'),
                    InlineKeyboardButton(text='Text to Img', callback_data='text_to_img'),
                    InlineKeyboardButton(text='Img to Text', callback_data='img_to_text'),
                    InlineKeyboardButton(text='Img to PDF', callback_data='img_to_pdf'),
                    InlineKeyboardButton(text='PDF to Img', callback_data='pdf_to_img'),
                    InlineKeyboardButton(text='MP4 to Audio', callback_data='mp4_to_audio')
                ]
            ]
        )
        app.send_message(chat_id, "Sila pilih pilihan Convert:", reply_markup=markup)
    except Exception as e:
        logger.error(f"Ralat memaparkan submenu convert: {e}")

def show_broadcast_submenu(chat_id: int) -> None:
    """Tunjukkan pilihan submenu di bawah 'Broadcast'."""
    try:
        markup = InlineKeyboardMarkup(
            inline_keyboard=[
                [
                    InlineKeyboardButton(text='Broadcast User', callback_data='broadcast_user'),
                    InlineKeyboardButton(text='Broadcast Group', callback_data='broadcast_group'),
                    InlineKeyboardButton(text='Broadcast Channel', callback_data='broadcast_channel'),
                    InlineKeyboardButton(text='Broadcast All', callback_data='broadcast_all')
                ],
                [
                    InlineKeyboardButton(text='Schedule User', callback_data='schedule_user'),
                    InlineKeyboardButton(text='Schedule Group', callback_data='schedule_group'),
                    InlineKeyboardButton(text='Schedule Channel', callback_data='schedule_channel'),
                    InlineKeyboardButton(text='Schedule All', callback_data='schedule_all')
                ],
                [
                    InlineKeyboardButton(text='List Scheduled Jobs', callback_data='list_scheduled_jobs')
                ]
            ]
        )
        app.send_message(chat_id, "Sila pilih pilihan Broadcast:", reply_markup=markup)
    except Exception as e:
        logger.error(f"Ralat memaparkan submenu broadcast: {e}")

def show_chatgpt_submenu(chat_id: int) -> None:
    """Tunjukkan pilihan submenu di bawah 'ChatGPT'."""
    try:
        markup = InlineKeyboardMarkup(
            inline_keyboard=[
                [
                    InlineKeyboardButton(text='Generate Response', callback_data='generate_response'),
                    InlineKeyboardButton(text='Extract Info', callback_data='extract_info')
                ]
            ]
        )
        app.send_message(chat_id, "Sila pilih pilihan ChatGPT:", reply_markup=markup)
    except Exception as e:
        logger.error(f"Ralat memaparkan submenu ChatGPT: {e}")

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

if __name__ == "__main__":
    app.run()
