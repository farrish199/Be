import json
import os

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
