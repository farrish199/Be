from flask import Flask, request, jsonify
import json
import logging
import os
from typing import Dict
from datetime import datetime, timedelta
from payment import create_category, create_bill

app = Flask(__name__)
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Tempat menyimpan data pengguna
USER_DATA_FILE = 'userpaid_data.json'

def load_userpaid_data():
    """Muatkan data pengguna dari fail."""
    if os.path.exists(USER_DATA_FILE):
        with open(USER_DATA_FILE, 'r') as file:
            try:
                return json.load(file)
            except json.JSONDecodeError as e:
                logger.error(f"Ralat mendekod JSON dari fail: {e}")
                return {}
    return {}

def save_userpaid_data(user_data):
    """Simpan data pengguna ke dalam fail."""
    try:
        with open(USER_DATA_FILE, 'w') as file:
            json.dump(user_data, file, indent=4)
    except IOError as e:
        logger.error(f"Ralat menulis ke fail: {e}")

def load_premium_users() -> Dict[str, Dict[str, str]]:
    """Muatkan data pengguna premium dari fail JSON."""
    try:
        with open('userpaid_data.json', 'r') as file:
            return json.load(file)
    except FileNotFoundError:
        return {}
    except json.JSONDecodeError:
        logger.error("Gagal memuatkan data pengguna premium. Format JSON tidak sah.")
        return {}

def is_premium(user_id: int) -> bool:
    """Semak jika pengguna mempunyai langganan premium yang sah."""
    premium_users = load_premium_users()
    user_data = premium_users.get(str(user_id))
    
    if user_data:
        subscription_end = datetime.fromisoformat(user_data['subscription_end'])
        return datetime.now() < subscription_end
    
    return False
    
def set_premium_status(user_id: int, is_premium: bool) -> None:
    """Tetapkan status premium pengguna berdasarkan pembayaran."""
    premium_users = load_premium_users()
    
    if is_premium:
        # Set langganan tamat tempoh 30 hari dari sekarang sebagai contoh
        subscription_end = (datetime.now() + timedelta(days=30)).isoformat()
        premium_users[str(user_id)] = {"subscription_end": subscription_end}
    else:
        if str(user_id) in premium_users:
            del premium_users[str(user_id)]
    
    with open('userpaid_data.json', 'w') as file:
        json.dump(premium_users, file, indent=4)

@app.route('/payment_callback', methods=['POST'])
def payment_callback():
    """Tangani callback pembayaran dan kemas kini status pengguna."""
    try:
        data = request.json
        bill_code = data.get('billcode')
        status = data.get('status')
        order_id = data.get('order_id')

        if not order_id:
            logger.error("ID pesanan tiada dalam callback.")
            return jsonify({'status': 'error', 'message': 'ID pesanan tiada'}), 400

        user_id = int(order_id.split('_')[0])

        if status == '1':  # Berjaya
            user_data = load_userpaid_data()
            subscription_end = datetime.now() + timedelta(days=30)
            user_data[user_id] = {"subscription_end": subscription_end.isoformat()}
            save_userpaid_data(user_data)
            # Beritahu pengguna (melalui bot Telegram, dsb.)
            return jsonify({'status': 'success', 'message': 'Pembayaran berjaya'}), 200
        else:
            return jsonify({'status': 'failure', 'message': 'Pembayaran gagal'}), 400
    except Exception as e:
        logger.error(f"Pengendalian callback pembayaran gagal: {e}")
        return jsonify({'status': 'error', 'message': 'Ralat pelayan dalaman'}), 500

if __name__ == '__main__':
    app.run(port=5000)  # Jalankan pada port 5000 atau port yang sesuai
