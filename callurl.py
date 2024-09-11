from flask import Flask, request, jsonify
import json
import logging
import os
from datetime import datetime, timedelta

app = Flask(__name__)
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Tempat menyimpan data pengguna
USER_DATA_FILE = 'userpaid_data.json'

def load_user_data():
    """Muatkan data pengguna dari fail."""
    if os.path.exists(USER_DATA_FILE):
        with open(USER_DATA_FILE, 'r') as file:
            try:
                return json.load(file)
            except json.JSONDecodeError as e:
                logger.error(f"Ralat mendekod JSON dari fail: {e}")
                return {}
    return {}

def save_user_data(user_data):
    """Simpan data pengguna ke dalam fail."""
    try:
        with open(USER_DATA_FILE, 'w') as file:
            json.dump(user_data, file, indent=4)
    except IOError as e:
        logger.error(f"Ralat menulis ke fail: {e}")

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
            user_data = load_user_data()
            subscription_end = datetime.now() + timedelta(days=30)
            user_data[user_id] = {"subscription_end": subscription_end.isoformat()}
            save_user_data(user_data)
            # Beritahu pengguna (melalui bot Telegram, dsb.)
            return jsonify({'status': 'success', 'message': 'Pembayaran berjaya'}), 200
        else:
            return jsonify({'status': 'failure', 'message': 'Pembayaran gagal'}), 400
    except Exception as e:
        logger.error(f"Pengendalian callback pembayaran gagal: {e}")
        return jsonify({'status': 'error', 'message': 'Ralat pelayan dalaman'}), 500

if __name__ == '__main__':
    app.run(port=5000)  # Jalankan pada port 5000 atau port yang sesuai
