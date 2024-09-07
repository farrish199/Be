# txtoimg.py

from PIL import Image, ImageDraw, ImageFont
import io
import telebot

def text_to_image(text: str) -> io.BytesIO:
    """Convert text to an image and return it as a BytesIO object."""
    font_size = 20
    image_size = (800, 600)  # Width, Height
    image = Image.new('RGB', image_size, color='white')
    draw = ImageDraw.Draw(image)
    
    try:
        font = ImageFont.truetype("arial.ttf", font_size)
    except IOError:
        font = ImageFont.load_default()
    
    text_color = 'black'
    draw.text((10, 10), text, font=font, fill=text_color)
    
    img_bytes = io.BytesIO()
    image.save(img_bytes, format='PNG')
    img_bytes.seek(0)
    return img_bytes
