import io
from pdf2image import convert_from_path
from PIL import Image, ImageDraw, ImageFont
import pytesseract
from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import letter

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

def image_to_text(image_stream: io.BytesIO) -> str:
    """Convert an image to text using OCR and return the extracted text."""
    image = Image.open(image_stream)
    text = pytesseract.image_to_string(image)
    return text

def image_to_pdf(image_stream: io.BytesIO, output_stream: io.BytesIO) -> None:
    """Convert an image to PDF and write it to the output stream."""
    image = Image.open(image_stream)
    
    # Create a PDF in memory
    c = canvas.Canvas(output_stream, pagesize=letter)
    width, height = letter
    
    # Scale image to fit the page if needed
    img_width, img_height = image.size
    aspect = img_width / img_height
    if aspect > width / height:
        new_width = width
        new_height = width / aspect
    else:
        new_height = height
        new_width = height * aspect
    
    # Center the image
    x = (width - new_width) / 2
    y = (height - new_height) / 2
    
    # Save the image in memory and draw it on the PDF
    img_bytes = io.BytesIO()
    image.save(img_bytes, format='PNG')
    img_bytes.seek(0)
    
    c.drawImage(img_bytes, x, y, new_width, new_height)
    c.showPage()
    c.save()
    output_stream.seek(0)

def pdf_to_image(pdf_stream: io.BytesIO) -> io.BytesIO:
    """Convert a PDF to an image and return the image in a BytesIO stream."""
    pdf_stream.seek(0)  # Ensure the stream is at the beginning
    images = convert_from_path(pdf_stream, dpi=300)
    image_stream = io.BytesIO()
    
    # Assuming the PDF has one page and we convert only the first page to an image
    if images:
        image = images[0]
        image.save(image_stream, format='PNG')  # You can change 'PNG' to other formats if needed
        image_stream.seek(0)
    
    return image_stream
