import json
import os
import sqlite3
from datetime import datetime
import logging
from pyrogram import Client, filters
from pyrogram.types import Message

LIMITS_FILE = "limits.json"
DB_PATH = 'your_database_path.db'
ADMIN_USER_ID = os.getenv("ADMIN_USER_ID")

# Konfigurasi logger
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def set_daily_limit(user_id: int, feature: str, limit: int) -> None:
    """Tetapkan had harian untuk fungsi tertentu bagi pengguna versi percuma tertentu."""
    today = datetime.now().date()
    with sqlite3.connect(DB_PATH) as conn:
        cursor = conn.cursor()
        cursor.execute("""
            INSERT INTO daily_usage (user_id, feature, usage, limit, last_updated)
            VALUES (?, ?, 0, ?, ?)
            ON CONFLICT(user_id, feature) DO UPDATE SET
                limit = excluded.limit,
                last_updated = excluded.last_updated
        """, (user_id, feature, limit, today))
        conn.commit()

@app.on_message(filters.command('setdailylimit'))
def handle_set_daily_limit(client: Client, message: Message) -> None:
    """Tangani arahan /setdailylimit untuk menetapkan had harian bagi pengguna versi percuma tertentu."""
    try:
        # Periksa jika pengguna adalah admin
        if message.from_user.id != ADMIN_USER_ID:
            client.send_message(message.chat.id, "Hanya admin yang dibenarkan menetapkan had harian.")
            return
        
        # Parse input command
        command_parts = message.text.split()
        if len(command_parts) != 4:
            client.send_message(message.chat.id, "Format arahan tidak betul. Sila gunakan /setdailylimit {user_id} {hadlimit} {fungsi}.")
            return
        
        user_id = int(command_parts[1])
        limit = int(command_parts[2])
        feature = command_parts[3]

        # Tetapkan had harian
        set_daily_limit(user_id, feature, limit)

        client.send_message(message.chat.id, f"Had harian untuk {feature} bagi pengguna dengan ID {user_id} telah ditetapkan kepada {limit}.")
    
    except ValueError:
        client.send_message(message.chat.id, "Sila pastikan had limit dan user_id adalah nombor yang sah.")
    except Exception as e:
        logger.error(f"Ralat semasa menetapkan had harian: {e}")
        client.send_message(message.chat.id, "Maaf, terdapat ralat semasa menetapkan had harian.")

def load_limits() -> dict:
    """Muatkan had dari fail."""
    if os.path.exists(LIMITS_FILE):
        with open(LIMITS_FILE, "r") as file:
            return json.load(file)
    return {}

def save_limits(data: dict) -> None:
    """Simpan had ke dalam fail."""
    with open(LIMITS_FILE, "w") as file:
        json.dump(data, file, indent=2)

def initialize_user(user_id: int) -> None:
    """Inisialisasi had harian untuk pengguna baru."""
    limits = load_limits()
    user_id_str = str(user_id)
    
    if user_id_str not in limits:
        today = datetime.now().date().isoformat()
        limits[user_id_str] = {
            "convert": {"date": today, "count": 0, "limit": 5},
            "broadcast": {"date": today, "count": 0, "limit": 2},
            "auto_approve": {"date": today, "count": 0, "limit": 5},
            "downloader": {"date": today, "count": 0, "limit": 5},
            "chatgpt": {"date": today, "count": 0, "limit": 10}
        }
        save_limits(limits)

def check_daily_limit(user_id: int, feature: str) -> bool:
    """Semak jika pengguna telah melebihi had harian untuk fungsi tertentu."""
    limits = load_limits()
    user_id_str = str(user_id)
    
    today = datetime.now().date().isoformat()
    
    if user_id_str not in limits:
        initialize_user(user_id)  # Inisialisasi jika pengguna tidak ditemui
        limits = load_limits()  # Muatkan semula had selepas inisialisasi

    user_limits = limits.get(user_id_str, {})
    feature_limits = user_limits.get(feature, {})
    
    # Semak jika penggunaan harian wujud dan adalah untuk hari ini
    if feature_limits.get("date") == today:
        daily_limit = feature_limits.get("limit", 0)
        usage_count = feature_limits.get("count", 0)
        
        if usage_count >= daily_limit:
            return False  # Melebihi had harian
    
    return True  # Tidak melebihi had harian

def update_daily_usage(user_id: int, feature: str) -> None:
    """Kemaskini kiraan penggunaan harian untuk fungsi tertentu."""
    limits = load_limits()
    user_id_str = str(user_id)
    
    today = datetime.now().date().isoformat()
    
    if user_id_str not in limits:
        initialize_user(user_id)  # Inisialisasi jika pengguna tidak ditemui
        limits = load_limits()  # Muatkan semula had selepas inisialisasi

    user_limits = limits.get(user_id_str, {})
    feature_limits = user_limits.get(feature, {})
    
    # Inisialisasi data penggunaan harian jika tidak wujud
    if feature_limits.get("date") != today:
        feature_limits = {"date": today, "count": 0, "limit": 10}  # Tetapkan had harian mengikut keperluan
        user_limits[feature] = feature_limits
    
    # Tambah kiraan penggunaan
    feature_limits["count"] += 1
    limits[user_id_str] = user_limits
    save_limits(limits)
