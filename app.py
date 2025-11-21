import os
import random
from datetime import datetime
from flask import Flask, render_template, redirect, url_for, request, flash
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager, UserMixin, login_user, logout_user, login_required, current_user
from werkzeug.security import generate_password_hash, check_password_hash

app = Flask(__name__)
app.config['SECRET_KEY'] = 'escoba-drives-master-key-2025' 
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:////home/Yoeph/escoba_drivers/db_escoba.sqlite'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

db = SQLAlchemy(app)
login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = 'login'

# SUPERVISORES
SUPERVISORES_CONTACTO = [
    {'nombre': 'ANA', 'telefono': '34657042721'},
    {'nombre': 'JIMMY', 'telefono': '34665036569'},
    {'nombre': 'RAMON', 'telefono': '34617468557'}
]

class User(UserMixin, db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), unique=True, nullable=False)
    email = db.Column(db.String(100), unique=True, nullable=True)
    password_hash = db.Column(db.String(200), nullable=True)
    role = db.Column(db.String(20), default='Conductor') 
    fixed_days_off = db.Column(db.String(100), default='')
    current_status = db.Column(db.String(50), default='Baja Laboral') 
    last_escoba_date = db.Column(db.DateTime, nullable=True)
    is_registered = db.Column(db.Boolean, default=False)
    signup_pin = db.Column(db.String(10), nullable=True)

class GlobalSettings(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    current_escoba_name = db.Column(db.String(100), default='Ninguno')
    current_escoba2_name = db.Column(db.String(100), default=None)
    last_rotation_date = db.Column(db.DateTime, default=datetime.now)

@login_manager.user_loader
def load_user(user_id): return User.query.get(int(user_id))

@app.route('/')
def index(): return redirect(url_for('dashboard')) if current_user.is_authenticated else redirect(url_for('login'))

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        ident = request.form.get('email').strip().lower(); pwd = request.form.get('password')
        user = User.query.filter((User.email == ident) | (User.name == ident.upper())).first()
        if user and user.password_hash and check_password_hash(user.password_hash, pwd):
            login_user(user); return redirect(url_for('dashboard'))
        else: flash('Datos incorrectos.', 'danger')
    return render_template('login.html')

@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        nombre = request.form.get('name'); email = request.form.get('email').strip().lower(); pwd = request.form.get('password'); pin = request.form.get('pin').strip()
        dias = ','.join(request.form.getlist('dias_libres'))
        user = User.query.filter_by(name=nombre).first()
        if not user: flash('Usuario no encontrado.', 'danger')
        elif user.is_registered: flash('Cuenta ya activa.', 'warning'); return redirect(url_for('login'))
        elif user.signup_pin != pin: flash('PIN incorrecto.', 'danger')
        else:
            user.email = email; user.password_hash = generate_password_hash(pwd); user.fixed_days_off = dias; user.current_status = 'Activo'; user.is_registered = True
            db.session.commit(); flash('Activado.', 'success'); return redirect(url_for('login'))
    nombres = User.query.filter_by(is_registered=False, role='Conductor').all()
    return render_template('register.html', lista_nombres=nombres, supervisores=SUPERVISORES_CONTACTO)

@app.route('/reset_password', methods=['GET', 'POST'])
def reset_password():
    if request.method == 'POST':
        email = request.form.get('email').strip().lower(); pin = request.form.get('pin').strip(); new_pwd = request.form.get('new_password')
        user = User.query.filter_by(email=email).first()
        if user and user.signup_pin == pin:
            user.password_hash = generate_password_hash(new_pwd); db.session.commit()
            flash('Contraseña cambiada.', 'success'); return redirect(url_for('login'))
        else: flash('Email o PIN incorrectos.', 'danger')
    return render_template('reset_password.html', supervisores=SUPERVISORES_CONTACTO)

@app.route('/change_password_internal', methods=['POST'])
@login_required
def change_password_internal():
    new_pwd = request.form.get('new_password')
    if new_pwd:
        current_user.password_hash = generate_password_hash(new_pwd); db.session.commit()
        flash('Clave actualizada.', 'success')
    return redirect(url_for('dashboard'))

@app.route('/dashboard')
@login_required
def dashboard():
    settings = GlobalSettings.query.first()
    drivers = User.query.filter_by(role='Conductor').all()
    drivers.sort(key=lambda x: x.current_status != 'Activo')
    dias_map = {0: 'Lunes', 1: 'Martes', 2: 'Miércoles', 3: 'Jueves', 4: 'Viernes', 5: 'Sábado', 6: 'Domingo'}
    return render_template('dashboard.html', user=current_user, drivers=drivers, 
                           escoba1=settings.current_escoba_name, escoba2=settings.current_escoba2_name, 
                           hoy_dia=dias_map[datetime.now().weekday()])

@app.route('/update_status', methods=['POST'])
@login_required
def update_status():
    if current_user.role == 'Conductor':
        current_user.current_status = request.form.get('status'); db.session.commit(); flash('Estado actualizado.', 'info')
    return redirect(url_for('dashboard'))

# --- RUTA QUE FALTABA (ADMIN FORCE CHANGE) ---
@app.route('/admin/force_status_change/<int:driver_id>', methods=['POST'])
@login_required
def force_status_change(driver_id):
    if current_user.role != 'Supervisor': return '403', 403
    driver = User.query.get(driver_id)
    new_status = request.form.get('status')
    if driver and new_status:
        driver.current_status = new_status; db.session.commit()
        flash(f'Estado cambiado a {new_status}', 'info')
    return redirect(url_for('dashboard'))

@app.route('/admin/next_turn', methods=['POST'])
@login_required
def next_turn():
    if current_user.role != 'Supervisor': return '403', 403
    settings = GlobalSettings.query.first()
    drivers = User.query.filter_by(role='Conductor').all()
    hoy = {0: 'Lunes', 1: 'Martes', 2: 'Miércoles', 3: 'Jueves', 4: 'Viernes', 5: 'Sábado', 6: 'Domingo'}[datetime.now().weekday()]
    candidatos = [d for d in drivers if d.current_status == 'Activo' and hoy not in d.fixed_days_off]
    if not candidatos: flash('Nadie disponible hoy.', 'danger')
    else:
        def get_date(x): return x.last_escoba_date if x.last_escoba_date else datetime(1900,1,1)
        candidatos.sort(key=lambda x: (get_date(x), x.id))
        elegido = candidatos[0]
        settings.current_escoba_name = elegido.name; settings.current_escoba2_name = None; settings.last_rotation_date = datetime.now()
        elegido.last_escoba_date = datetime.now(); db.session.commit()
        flash(f'Nuevo Turno: {elegido.name}', 'success')
    return redirect(url_for('dashboard'))

@app.route('/admin/add_extra_turn', methods=['POST'])
@login_required
def add_extra_turn():
    if current_user.role != 'Supervisor': return '403', 403
    settings = GlobalSettings.query.first()
    if settings.current_escoba2_name: flash('Ya hay refuerzo.', 'warning'); return redirect(url_for('dashboard'))
    drivers = User.query.filter_by(role='Conductor').all()
    hoy = {0: 'Lunes', 1: 'Martes', 2: 'Miércoles', 3: 'Jueves', 4: 'Viernes', 5: 'Sábado', 6: 'Domingo'}[datetime.now().weekday()]
    candidatos = [d for d in drivers if d.current_status == 'Activo' and hoy not in d.fixed_days_off and d.name != settings.current_escoba_name]
    if not candidatos: flash('No quedan conductores.', 'danger')
    else:
        def get_date(x): return x.last_escoba_date if x.last_escoba_date else datetime(1900,1,1)
        candidatos.sort(key=lambda x: (get_date(x), x.id))
        elegido = candidatos[0]
        settings.current_escoba2_name = elegido.name; elegido.last_escoba_date = datetime.now()
        db.session.commit(); flash(f'Refuerzo: {elegido.name}', 'success')
    return redirect(url_for('dashboard'))

@app.route('/admin/add_driver', methods=['POST'])
@login_required
def add_driver():
    if current_user.role != 'Supervisor': return '403', 403
    name = request.form.get('new_driver_name').strip().upper()
    if not name: return redirect(url_for('dashboard'))
    if User.query.filter_by(name=name).first(): flash('Ya existe.', 'warning')
    else:
        pin = str(random.randint(1000, 9999))
        db.session.add(User(name=name, role='Conductor', current_status='Baja Laboral', is_registered=False, signup_pin=pin))
        db.session.commit(); flash(f'Añadido: {name}', 'success')
    return redirect(url_for('dashboard'))

@app.route('/admin/delete_driver/<int:driver_id>', methods=['POST'])
@login_required
def delete_driver(driver_id):
    if current_user.role != 'Supervisor': return '403', 403
    driver = User.query.get(driver_id)
    if driver and driver.role == 'Conductor':
        s = GlobalSettings.query.first()
        if driver.name == s.current_escoba_name or driver.name == s.current_escoba2_name: flash('No puedes borrar al escoba actual.', 'danger')
        else: db.session.delete(driver); db.session.commit(); flash(f'Eliminado: {driver.name}', 'success')
    return redirect(url_for('dashboard'))

@app.route('/logout')
@login_required
def logout(): logout_user(); return redirect(url_for('login'))

if __name__ == '__main__': app.run(debug=True)
