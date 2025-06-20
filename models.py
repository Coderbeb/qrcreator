from flask_sqlalchemy import SQLAlchemy

db = SQLAlchemy()

class Work(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(120))
    description = db.Column(db.Text)
    images = db.Column(db.Text)  # Comma-separated filenames

class QRCode(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    qr_type = db.Column(db.String(20))  # 'link', 'image', 'offer'
    links = db.Column(db.Text)          # Comma-separated links
    images = db.Column(db.Text)         # Comma-separated image filenames
    offer = db.Column(db.String(120))
    one_time = db.Column(db.Boolean, default=True)
    used = db.Column(db.Boolean, default=False)
    qr_image = db.Column(db.String(120))

class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    email = db.Column(db.String(120))
    phone = db.Column(db.String(20))
    qr_id = db.Column(db.Integer)