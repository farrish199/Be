import os
import json
import requests
from typing import Dict, Optional
import telebot
from config import PAID_USER_IDS, TOYYIBPAY_SECRET_KEY

# Define type aliases for better readability
UserData = Dict[str, Optional[int]]
PaymentStatus = Dict[str, str]

# Constants for bot limits
FREE_VERSION_LIMIT = 1
PREMIUM_VERSION_LIMIT = 5

def get_user_bot_limits() -> Dict[str, int]:
    """Retrieve default bot limits for users."""
    return {
        'freemium_bots': 0,
        'premium_bots': 0
    }

def is_user_paid(user_id: int) -> bool:
    """Check if the user has paid and is allowed to clone the bot."""
    return user_id in PAID_USER_IDS

def get_user_data(user_id: int) -> UserData:
    """Load user data from file."""
    user_data = load_user_data()
    return user_data.get(str(user_id), {})

def load_user_data() -> Dict[str, UserData]:
    """Load user data from file."""
    if os.path.exists('user_data.json'):
        with open('user_data.json', 'r') as file:
            return json.load(file)
    return {}

def save_user_data(user_data: Dict[str, UserData]) -> None:
    """Save user data to file."""
    with open('user_data.json', 'w') as file:
        json.dump(user_data, file, indent=4)

def clone_bot(message: telebot.types.Message, bot: telebot.TeleBot) -> None:
    """Handle bot cloning based on user payment status and limits."""
    user_id = str(message.from_user.id)
    user_data = get_user_data(message.from_user.id)
    
    # Initialize user data if not present
    if not user_data:
        user_data = get_user_bot_limits()

    if is_user_paid(message.from_user.id):
        # Check and update bot count for paid users
        if user_data.get('premium_bots', 0) < PREMIUM_VERSION_LIMIT:
            user_data['premium_bots'] = user_data.get('premium_bots', 0) + 1
            save_user_data({user_id: user_data})
            bot.reply_to(message, "Your bot is being cloned...")
        else:
            bot.reply_to(message, "You have reached the maximum number of bot clones allowed for premium users.")
    else:
        # Check and update bot count for free users
        if user_data.get('freemium_bots', 0) < FREE_VERSION_LIMIT:
            user_data['freemium_bots'] = user_data.get('freemium_bots', 0) + 1
            save_user_data({user_id: user_data})
            bot.reply_to(message, "Your bot is being cloned...")
        else:
            bot.reply_to(message, "You have reached the maximum number of bot clones allowed for free users.")

def fetch_additional_data(api_url: str) -> Dict[str, str]:
    """Fetch additional data from an external API."""
    try:
        response = requests.get(api_url)
        response.raise_for_status()  # Raise HTTPError for bad responses
        return response.json()
    except requests.RequestException as e:
        # Log the error and return an error message
        logger.error(f"Error fetching data from API: {e}")
        return {"error": "Failed to fetch data"}

# Logger configuration
import logging
logger = logging.getLogger(__name__)
