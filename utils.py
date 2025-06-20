import random
import smtplib
import os
from email.mime.text import MIMEText
from flask import flash
import qrcode
from werkzeug.utils import secure_filename

# Allowed file extensions for uploads
ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif'}


def allowed_file(filename):
    """Check if a file is an allowed type (image)."""
    return '.' in filename and \
           filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS


def generate_otp():
    """Generate a 6-digit numeric OTP."""
    return str(random.randint(100000, 999999))


def send_otp(email, otp):
    """Send OTP to user's email using Gmail SMTP."""
    msg = MIMEText(f"Your OTP is: {otp}")
    msg['Subject'] = 'Your OTP for QR Creator'
    msg['From'] = os.environ.get("EMAIL_USER")
    msg['To'] = email

    try:
        with smtplib.SMTP('smtp.gmail.com', 587) as server:
            server.starttls()
            server.login(os.environ.get("EMAIL_USER"), os.environ.get("EMAIL_PASS"))
            server.send_message(msg)
            print(f"OTP sent to {email}")
    except Exception as e:
        print(f"Failed to send OTP to {email}: {e}")
        flash("Failed to send OTP. Please try again later.", "danger")


def verify_otp(sent_otp, user_otp):
    """Verify that the OTP matches."""
    return sent_otp == user_otp


def generate_qr(data, filename):
    """Generate a QR code from the provided data."""
    qr = qrcode.QRCode(
        version=1,
        box_size=10,
        border=5
    )
    qr.add_data(data)
    qr.make(fit=True)
    img = qr.make_image(fill_color='black', back_color='white')
    img.save(filename)
