def create_payment_link(amount: float, description: str, user_id: int) -> str:
    """Create a payment link using ToyyibPay."""
    headers = {
        'Authorization': f'Bearer {TOYYIBPAY_API_KEY}',
        'Content-Type': 'application/json'
    }
    payload = {
        'amount': amount,
        'description': description,
        'redirect_url': f'https://yourdomain.com/payment_success?user_id={user_id}'
    }
    response = requests.post(f'{TOYYIBPAY_URL}/create_payment_link', headers=headers, json=payload)
    data = response.json()
    if response.status_code == 200:
        return data['payment_link']
    else:
        logger.error(f"ToyyibPay error: {data.get('message')}")
        return ""

def verify_payment(transaction_id: str) -> bool:
    """Verify payment with ToyyibPay."""
    headers = {
        'Authorization': f'Bearer {TOYYIBPAY_SECRET_KEY}',
        'Content-Type': 'application/json'
    }
    response = requests.get(f'{TOYYIBPAY_URL}/verify_payment/{transaction_id}', headers=headers)
    data = response.json()
    return data.get('status') == 'success'

@app.on_message(filters.command("payment_success"))
def handle_payment_success(client: Client, message: Message) -> None:
    """Handle successful payment notification."""
    try:
        user_id = int(message.text.split('user_id=')[1].strip())
        transaction_id = message.text.split('transaction_id=')[1].strip()
        
        if verify_payment(transaction_id):
            update_user_data(user_id, 'version', 'premium_version')
            client.send_message(message.chat.id, "Pembayaran anda telah disahkan. Langganan Premium anda telah diaktifkan.")
        else:
            client.send_message(message.chat.id, "Pembayaran anda tidak dapat disahkan. Sila hubungi sokongan.")
    except Exception as e:
        logger.error(f"Error handling payment success: {e}")
