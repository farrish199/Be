import telebot
from telebot.types import InlineKeyboardButton, InlineKeyboardMarkup

def get_main_keyboard() -> InlineKeyboardMarkup:
    """Create the main menu keyboard."""
    markup = InlineKeyboardMarkup()
    button_service = InlineKeyboardButton(text='Service', callback_data='service')
    button_dev_bot = InlineKeyboardButton(text='Dev Bot', callback_data='dev_bot')
    button_support_bot = InlineKeyboardButton(text='Support Bot', callback_data='support_bot')
    button_clone_bot = InlineKeyboardButton(text='Clone Bot', callback_data='clone_bot')
    markup.add(button_service, button_dev_bot, button_support_bot, button_clone_bot)
    return markup

def get_submenu_keyboard(option: str) -> InlineKeyboardMarkup:
    """Create the submenu keyboard based on the given option."""
    markup = InlineKeyboardMarkup()
    if option == 'service':
        button_free_version = InlineKeyboardButton(text='Free Version', callback_data='free_version')
        button_premium_version = InlineKeyboardButton(text='Premium Version', callback_data='premium_version')
        markup.add(button_free_version, button_premium_version)
    elif option in ['free_version', 'premium_version']:
        button_convert = InlineKeyboardButton(text='Convert', callback_data=f'{option}_convert')
        button_broadcast = InlineKeyboardButton(text='Broadcast', callback_data=f'{option}_broadcast')
        button_auto_approve = InlineKeyboardButton(text='Auto Approve', callback_data=f'{option}_auto_approve')
        button_downloader = InlineKeyboardButton(text='Downloader', callback_data=f'{option}_downloader')
        button_chatgpt = InlineKeyboardButton(text='ChatGPT', callback_data=f'{option}_chatgpt')
        markup.add(button_convert, button_broadcast, button_auto_approve, button_downloader, button_chatgpt)
    elif option == 'convert':
        button_bug_vless = InlineKeyboardButton(text='Bug Vless', callback_data='bug_vless')
        button_text_to_img = InlineKeyboardButton(text='Text to Img', callback_data='text_to_img')
        button_img_to_text = InlineKeyboardButton(text='Img to Text', callback_data='img_to_text')
        button_img_to_pdf = InlineKeyboardButton(text='Img to PDF', callback_data='img_to_pdf')
        button_pdf_to_img = InlineKeyboardButton(text='PDF to Img', callback_data='pdf_to_img')
        button_mp4_to_audio = InlineKeyboardButton(text='MP4 to Audio', callback_data='mp4_to_audio')
        markup.add(button_bug_vless, button_text_to_img, button_img_to_text, button_img_to_pdf, button_pdf_to_img, button_mp4_to_audio)
    elif option == 'downloader':
        button_fb = InlineKeyboardButton(text='FB', callback_data='downloader_fb')
        button_ig = InlineKeyboardButton(text='IG', callback_data='downloader_ig')
        button_tg = InlineKeyboardButton(text='TG', callback_data='downloader_tg')
        button_tt = InlineKeyboardButton(text='TT', callback_data='downloader_tt')
        button_yt = InlineKeyboardButton(text='YT', callback_data='downloader_yt')
        markup.add(button_fb, button_ig, button_tg, button_tt, button_yt)
    elif option == 'broadcast':
        button_broadcast_user = InlineKeyboardButton(text='Broadcast User', callback_data='broadcast_user')
        button_broadcast_group = InlineKeyboardButton(text='Broadcast Group', callback_data='broadcast_group')
        button_broadcast_channel = InlineKeyboardButton(text='Broadcast Channel', callback_data='broadcast_channel')
        button_broadcast_all = InlineKeyboardButton(text='Broadcast All', callback_data='broadcast_all')
        button_schedule_user = InlineKeyboardButton(text='Schedule User', callback_data='schedule_user')
        button_schedule_group = InlineKeyboardButton(text='Schedule Group', callback_data='schedule_group')
        button_schedule_channel = InlineKeyboardButton(text='Schedule Channel', callback_data='schedule_channel')
        button_schedule_all = InlineKeyboardButton(text='Schedule All', callback_data='schedule_all')
        markup.add(button_broadcast_user, button_broadcast_group, button_broadcast_channel, button_broadcast_all,
                    button_schedule_user, button_schedule_group, button_schedule_channel, button_schedule_all)
    return markup

def get_conversion_keyboard() -> telebot.types.ReplyKeyboardMarkup:
    """Create a keyboard for conversion options."""
    markup = telebot.types.ReplyKeyboardMarkup(resize_keyboard=True)
    buttons = ["Digi BS", "Digi XL", "UmoFunz XL", "Maxis UL", "Unifi XL", "Yes XL", "Celcom XL", "Booster 1", "Booster 2"]
    markup.add(*buttons)
    return markup

SUBMENU_OPTIONS = {
    'service': get_submenu_keyboard('service'),
    'free_version': get_submenu_keyboard('free_version'),
    'premium_version': get_submenu_keyboard('premium_version'),
    'downloader': get_submenu_keyboard('downloader'),
    'broadcast': get_submenu_keyboard('broadcast'),
    'convert': get_submenu_keyboard('convert'),
}
