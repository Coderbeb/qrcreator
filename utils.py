import random
import smtplib
from email.mime.text import MIMEText
import qrcode
import os

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in {'png', 'jpg', 'jpeg', 'gif'}

def generate_otp():
    return str(random.randint(100000, 999999))

def send_otp(email, otp):
    # For demo: print OTP to console. Replace with real email sending in production.
    print(f"OTP for {email}: {otp}")
    # Example for real email sending (configure SMTP as needed)
    # msg = MIMEText(f"Your OTP is: {otp}")
    # msg['Subject'] = 'Your OTP for qrcreator'
    # msg['From'] = 'your@email.com'
    # msg['To'] = email
    # with smtplib.SMTP('smtp.gmail.com', 587) as server:
    #     server.starttls()
    #     server.login('your@email.com', 'yourpassword')
    #     server.send_message(msg)

def verify_otp(sent_otp, user_otp):
    return sent_otp == user_otp

def generate_qr(data, filename):
    img = qrcode.make(data)
    img.save(filename)