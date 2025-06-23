from flask import Flask, render_template, request, redirect, url_for, session, flash
from werkzeug.security import generate_password_hash, check_password_hash
import os
from datetime import datetime
import secrets
import re

app = Flask(__name__)
app.config['SECRET_KEY'] = 'supersecretkey'
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///db.sqlite3'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

from models import db, User, InviteCode, Request

db.init_app(app)

with app.app_context():
    db.create_all()
    # Автоматическое создание админа
    ADMIN_EMAIL = 'admin@rifk7.com'
    ADMIN_PASSWORD = 'admin1234'
    if not User.query.filter_by(email=ADMIN_EMAIL).first():
        admin = User(email=ADMIN_EMAIL, password=generate_password_hash(ADMIN_PASSWORD), role='admin')
        db.session.add(admin)
        db.session.commit()

@app.route('/')
def index():
    # Пример новостей и преимуществ (можно заменить на загрузку из БД)
    news = [
        {"date": "2024-06-01", "text": "Обновление защиты и интерфейса."},
        {"date": "2024-05-25", "text": "Добавлены новые тарифы."},
        {"date": "2024-05-20", "text": "Запуск проекта."}
    ]
    features = [
        "Закрытая регистрация по инвайт-коду",
        "Современный минималистичный дизайн",
        "Личный кабинет с настройками",
        "Безопасность и приватность"
    ]
    tariffs = [
        {"name": "Basic", "desc": "7 дней доступа", "price": "199₽"},
        {"name": "Premium", "desc": "30 дней доступа", "price": "499₽"},
        {"name": "Lifetime", "desc": "Пожизненный доступ", "price": "1499₽"}
    ]
    return render_template('index.html', news=news, features=features, tariffs=tariffs)

@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        email = request.form['email']
        password = request.form['password']
        code = request.form['invite_code']
        # Проверка email
        if not re.match(r"^[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}$", email):
            flash('Некорректный email', 'danger')
            return redirect(url_for('register'))
        invite = InviteCode.query.filter_by(code=code, used=False).first()
        if not invite:
            flash('Неверный или уже использованный инвайт-код', 'danger')
            return redirect(url_for('register'))
        if User.query.filter_by(email=email).first():
            flash('Пользователь с таким email уже существует', 'danger')
            return redirect(url_for('register'))
        hashed_pw = generate_password_hash(password)
        user = User(email=email, password=hashed_pw, invite_code=invite)
        invite.used = True
        db.session.add(user)
        db.session.commit()
        flash('Регистрация успешна! Войдите.', 'success')
        return redirect(url_for('login'))
    return render_template('register.html')

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        email = request.form['email']
        password = request.form['password']
        user = User.query.filter_by(email=email).first()
        if user and check_password_hash(user.password, password):
            session['user_id'] = user.id
            session['role'] = user.role
            flash('Вход выполнен', 'success')
            return redirect(url_for('dashboard'))
        flash('Неверные данные', 'danger')
        return redirect(url_for('login'))
    return render_template('login.html')

@app.route('/logout')
def logout():
    session.clear()
    flash('Вы вышли из аккаунта', 'success')
    return redirect(url_for('index'))

@app.route('/dashboard')
def dashboard():
    if 'user_id' not in session:
        return redirect(url_for('login'))
    user = User.query.get(session['user_id'])
    return render_template('dashboard.html', user=user)

@app.route('/contacts')
def contacts():
    return render_template('contacts.html')

@app.route('/product')
def product():
    return render_template('product.html')

@app.route('/status')
def status():
    return render_template('status.html')

@app.route('/admin', methods=['GET', 'POST'])
def admin():
    if session.get('role') != 'admin':
        flash('Доступ только для администратора', 'danger')
        return redirect(url_for('index'))
    users = User.query.order_by(User.id.desc()).all()
    codes = InviteCode.query.order_by(InviteCode.id.desc()).all()
    new_code = None
    if request.method == 'POST':
        code = secrets.token_hex(8)
        invite = InviteCode(code=code)
        db.session.add(invite)
        db.session.commit()
        new_code = code
        codes = InviteCode.query.order_by(InviteCode.id.desc()).all()
    return render_template('admin.html', users=users, codes=codes, new_code=new_code)

if __name__ == '__main__':
    app.run(debug=True) 