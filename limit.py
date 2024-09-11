import sqlite3
from datetime import datetime

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
