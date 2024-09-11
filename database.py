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

@app.on_message(filters.new_chat_members)
def handle_new_chat_member(client: Client, message: Message) -> None:
    """Tangani ahli baru yang menyertai group/channel dan luluskan mereka secara automatik."""
    try:
        if message.new_chat_members:
            for member in message.new_chat_members:
                if member.id == client.get_me().id:
                    group_id = message.chat.id
                    save_auto_approve_group_id(group_id)
                    client.send_message(group_id, "Auto Approve kini diaktifkan untuk group/channel ini.")
                    break

        group_id = get_auto_approve_group_id()
        if group_id and message.chat.id == group_id:
            client.approve_chat_join_request(message.chat.id, message.from_user.id)
    except Exception as e:
        logger.error(f"Ralat mengendalikan ahli baru: {e}")
