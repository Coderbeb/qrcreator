from flask import Flask, render_template, request, redirect, url_for, session, flash, send_file
from werkzeug.utils import secure_filename
import os, io, zipfile
from models import db, User, Work, QRCode
from utils import send_otp, verify_otp, allowed_file, generate_otp, generate_qr

app = Flask(__name__)

app.secret_key = os.environ.get("SECRET_KEY", "your_secret_key")
if 'DATABASE_URL' in os.environ:
    app.config['SQLALCHEMY_DATABASE_URI'] = os.environ['DATABASE_URL'].replace('postgres://', 'postgresql://')
else:
    app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///qrcreator.db'

app.config['UPLOAD_FOLDER'] = 'static/images'
os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)
db.init_app(app)

with app.app_context():
    db.create_all()

@app.route('/')
def index():
    works = Work.query.all()
    return render_template('index.html', works=works)

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        if request.form['username'] == 'admin' and request.form['password'] == 'admin123':
            session['admin'] = True
            return redirect(url_for('admin'))
        else:
            flash('Invalid credentials', 'danger')
    return render_template('login.html')

@app.route('/logout')
def logout():
    session.pop('admin', None)
    return redirect(url_for('index'))

@app.route('/admin')
def admin():
    if not session.get('admin'):
        return redirect(url_for('login'))
    works = Work.query.all()
    qrcodes = QRCode.query.all()
    return render_template('admin.html', works=works, qrcodes=qrcodes)

@app.route('/add_work', methods=['GET', 'POST'])
def add_work():
    if not session.get('admin'):
        return redirect(url_for('login'))
    if request.method == 'POST':
        title = request.form['title']
        description = request.form['description']
        images = []
        files = request.files.getlist('images')
        for file in files:
            if file and allowed_file(file.filename):
                filename = secure_filename(file.filename)
                file.save(os.path.join(app.config['UPLOAD_FOLDER'], filename))
                images.append(filename)
        work = Work(title=title, description=description, images=','.join(images))
        db.session.add(work)
        db.session.commit()
        return redirect(url_for('admin'))
    return render_template('work_form.html', action='Add')

@app.route('/edit_work/<int:work_id>', methods=['GET', 'POST'])
def edit_work(work_id):
    if not session.get('admin'):
        return redirect(url_for('login'))
    work = Work.query.get_or_404(work_id)
    if request.method == 'POST':
        work.title = request.form['title']
        work.description = request.form['description']
        files = request.files.getlist('images')
        images = work.images.split(',') if work.images else []
        for file in files:
            if file and allowed_file(file.filename):
                filename = secure_filename(file.filename)
                file.save(os.path.join(app.config['UPLOAD_FOLDER'], filename))
                images.append(filename)
        work.images = ','.join(images)
        db.session.commit()
        return redirect(url_for('admin'))
    return render_template('work_form.html', action='Edit', work=work)

@app.route('/delete_work/<int:work_id>')
def delete_work(work_id):
    if not session.get('admin'):
        return redirect(url_for('login'))
    work = Work.query.get_or_404(work_id)
    db.session.delete(work)
    db.session.commit()
    return redirect(url_for('admin'))

@app.route('/add_qr', methods=['GET', 'POST'])
def add_qr():
    if not session.get('admin'):
        return redirect(url_for('login'))
    if request.method == 'POST':
        qr_type = request.form['qr_type']
        links = request.form.get('links', '').strip().splitlines() if qr_type == "link" else []
        images = []
        files = request.files.getlist('images')
        for file in files:
            if file and allowed_file(file.filename):
                filename = secure_filename(file.filename)
                file.save(os.path.join(app.config['UPLOAD_FOLDER'], filename))
                images.append(filename)
        offer = request.form.get('offer', '')
        one_time = True if request.form.get('one_time') == 'on' else False
        quantity = int(request.form.get('quantity', 1))

        zip_buffer = io.BytesIO()
        with zipfile.ZipFile(zip_buffer, 'w') as zip_file:
            for i in range(quantity):
                qr = QRCode(
                    qr_type=qr_type,
                    links=','.join(links),
                    images=','.join(images),
                    offer=offer,
                    one_time=one_time,
                    used=False
                )
                db.session.add(qr)
                db.session.flush()
                qr_url = url_for('scan_qr', qr_id=qr.id, _external=True)
                qr_image_filename = f"qr_{qr.id}.png"
                qr_image_path = os.path.join(app.config['UPLOAD_FOLDER'], qr_image_filename)
                generate_qr(qr_url, qr_image_path)
                qr.qr_image = qr_image_filename
                db.session.flush()
                zip_file.write(qr_image_path, qr_image_filename)
            db.session.commit()
        zip_buffer.seek(0)
        return send_file(zip_buffer, as_attachment=True, download_name='qr_codes.zip', mimetype='application/zip')
    return render_template('qr_form.html')

@app.route('/delete_qr/<int:qr_id>')
def delete_qr(qr_id):
    if not session.get('admin'):
        return redirect(url_for('login'))
    qr = QRCode.query.get_or_404(qr_id)
    db.session.delete(qr)
    db.session.commit()
    return redirect(url_for('admin'))

@app.route('/scan/<int:qr_id>', methods=['GET', 'POST'])
def scan_qr(qr_id):
    qr = QRCode.query.get_or_404(qr_id)
    if request.method == 'POST':
        first_name = request.form['first_name']
        last_name = request.form['last_name']
        city = request.form['city']
        phone = request.form['phone']
        email = request.form['email']
        user = User.query.filter_by(email=email, qr_id=qr_id).first()
        if user:
            flash('You have already registered with this QR code.', 'danger')
            return render_template('sorry.html')
        otp = generate_otp()
        send_otp(email, otp)
        session['pending_user'] = {
            'first_name': first_name,
            'last_name': last_name,
            'city': city,
            'phone': phone,
            'email': email,
            'qr_id': qr_id,
            'otp': otp
        }
        return redirect(url_for('otp_verify'))
    return render_template('register.html', qr=qr)

@app.route('/otp', methods=['GET', 'POST'])
def otp_verify():
    pending = session.get('pending_user')
    if not pending:
        return redirect(url_for('index'))
    if request.method == 'POST':
        user_otp = request.form['otp']
        if verify_otp(pending['otp'], user_otp):
            user = User(
                first_name=pending['first_name'],
                last_name=pending['last_name'],
                city=pending['city'],
                phone=pending['phone'],
                email=pending['email'],
                qr_id=pending['qr_id']
            )
            db.session.add(user)
            db.session.commit()
            qr = QRCode.query.get(pending['qr_id'])
            if qr.one_time and qr.used:
                flash('This offer has already been claimed.', 'danger')
                return render_template('sorry.html')
            if qr.one_time:
                qr.used = True
                db.session.commit()
            session.pop('pending_user')
            if qr.offer:
                return render_template('offer.html', offer=qr.offer)
            elif qr.links:
                links = qr.links.split(',')
                return render_template('show_links.html', links=links)
            elif qr.images:
                images = qr.images.split(',')
                return render_template('show_images.html', images=images)
            else:
                return render_template('sorry.html')
        else:
            flash('Invalid OTP. Please try again.', 'danger')
    return render_template('otp.html')

@app.route('/analytics')
def analytics():
    if not session.get('admin'):
        return redirect(url_for('login'))
    users = User.query.all()
    qrcodes = QRCode.query.all()
    return render_template('analytics.html', users=users, qrcodes=qrcodes)

if __name__ == '__main__':
    app.run(debug=True)
