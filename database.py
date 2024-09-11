import json
import os

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
        
def save_auto_approve_group_id(group_id: int) -> None:
    """Simpan ID group/channel untuk kelulusan automatik."""
    try:
        with open('auto_approve_group_id.txt', 'w') as f:
            f.write(str(group_id))
    except Exception as e:
        logger.error(f"Ralat menyimpan ID group/channel auto approve: {e}")

def get_auto_approve_group_id() -> int:
    """Muatkan ID kumpulan dari fail."""
    try:
        if os.path.exists('auto_approve_group_id.txt'):
            with open('auto_approve_group_id.txt', 'r') as f:
                return int(f.read().strip())
        return 0
    except Exception as e:
        logger.error(f"Ralat mendapatkan ID group/channel auto approve: {e}")
        return 0
