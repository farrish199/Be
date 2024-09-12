import json
import os
import sqlite3
from datetime import datetime

LIMITS_FILE = "limits.json"
DB_PATH = 'your_database_path.db'  # Gantikan dengan laluan sebenar kepada pangkalan data anda

def set_daily_limit(user_id: int, feature: str, limit: int) -> None:
    """Tetapkan had harian untuk fungsi tertentu bagi pengguna versi percuma tertentu."""
    today = datetime.now().date()
    with sqlite3.connect(DB_PATH) as conn:
        cursor = conn.cursor()
        cursor.execute("""
            INSERT INTO daily_usage (user_id, feature, usage, limit, last_updated)
            VALUES (?, ?, 0, ?, ?)
            ON CONFLICT(user_id, feature) DO UPDATE SET
                limit = ?,
                last_updated = ?
            WHERE user_id = ? AND feature = ?
        """, (user_id, feature, limit, today, limit, today, user_id, feature))
        conn.commit()

@app.on_message(filters.command('setdailylimit'))
def handle_set_daily_limit(client: Client, message: Message) -> None:
    """Tangani arahan /setdailylimit untuk menetapkan had harian bagi pengguna versi percuma tertentu."""
    try:
        # Periksa jika pengguna adalah admin
        if message.from_user.id != YOUR_ADMIN_USER_ID:
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
    """Load limits from a file."""
    if os.path.exists(LIMITS_FILE):
        with open(LIMITS_FILE, "r") as file:
            return json.load(file)
    return {}

def save_limits(data: dict) -> None:
    """Save limits to a file."""
    with open(LIMITS_FILE, "w") as file:
        json.dump(data, file, indent=2)

def initialize_user(user_id: int) -> None:
    """Initialize the daily limits for a new user."""
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

def check_daily_limit(user_id: int, feature: str, version: str) -> bool:
    """Check if the user has exceeded the daily limit for a feature."""
    limits = load_limits()
    user_id_str = str(user_id)
    
    today = datetime.now().date().isoformat()
    
    if user_id_str not in limits:
        initialize_user(user_id)  # Initialize if user is not found
        limits = load_limits()  # Reload limits after initialization

    user_limits = limits.get(user_id_str, {})
    feature_limits = user_limits.get(feature, {})
    
    # Check if daily usage exists and is for today
    if feature_limits.get("date") == today:
        daily_limit = feature_limits.get("limit", 0)
        usage_count = feature_limits.get("count", 0)
        
        if usage_count >= daily_limit:
            return False  # Exceeded daily limit
    
    return True  # Not exceeded daily limit

def update_daily_usage(user_id: int, feature: str) -> None:
    """Update the daily usage count for a feature."""
    limits = load_limits()
    user_id_str = str(user_id)
    
    today = datetime.now().date().isoformat()
    
    if user_id_str not in limits:
        initialize_user(user_id)  # Initialize if user is not found
        limits = load_limits()  # Reload limits after initialization

    user_limits = limits.get(user_id_str, {})
    feature_limits = user_limits.get(feature, {})
    
    # Initialize daily usage data if not already present
    if feature_limits.get("date") != today:
        feature_limits = {"date": today, "count": 0, "limit": 10}  # Set daily limit as needed
        user_limits[feature] = feature_limits
    
    # Increment usage count
    feature_limits["count"] += 1
    limits[user_id_str] = user_limits
    save_limits(limits)
