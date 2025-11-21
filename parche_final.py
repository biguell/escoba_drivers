import os
from datetime import datetime

# Usamos la carpeta actual (donde estás ahora mismo)
base_path = os.getcwd()
print(f"📍 Aplicando parche V4.2 en: {base_path}")

# --- APP.PY (CON GESTIÓN DE ESTADOS) ---
file_app_py = f"""# Actualizado el {datetime.now()}
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
    current_escoba_name = db.Column(db.String(100), default="Ninguno")
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
        dias = ",".join(request.form.getlist('dias_libres'))
        user = User.query.filter_by(name=nombre).first()
        if not user: flash('Usuario no encontrado.', 'danger')
        elif user.is_registered: flash('Cuenta ya activa.', 'warning'); return redirect(url_for('login'))
        elif user.signup_pin != pin: flash('PIN incorrecto.', 'danger')
        else:
            user.email = email; user.password_hash = generate_password_hash(pwd); user.fixed_days_off = dias; user.current_status = 'Activo'; user.is_registered = True
            db.session.commit(); flash('Activado.', 'success'); return redirect(url_for('login'))
    nombres = User.query.filter_by(is_registered=False, role='Conductor').all()
    return render_template('register.html', lista_nombres=nombres)

@app.route('/reset_password', methods=['GET', 'POST'])
def reset_password():
    if request.method == 'POST':
        email = request.form.get('email').strip().lower(); pin = request.form.get('pin').strip(); new_pwd = request.form.get('new_password')
        user = User.query.filter_by(email=email).first()
        if user and user.signup_pin == pin:
            user.password_hash = generate_password_hash(new_pwd); db.session.commit()
            flash('Contraseña cambiada.', 'success'); return redirect(url_for('login'))
        else: flash('Email o PIN incorrectos.', 'danger')
    return render_template('reset_password.html')

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
    dias_map = {{0: 'Lunes', 1: 'Martes', 2: 'Miércoles', 3: 'Jueves', 4: 'Viernes', 5: 'Sábado', 6: 'Domingo'}}
    return render_template('dashboard.html', user=current_user, drivers=drivers, 
                           escoba1=settings.current_escoba_name, 
                           escoba2=settings.current_escoba2_name, 
                           hoy_dia=dias_map[datetime.now().weekday()])

@app.route('/update_status', methods=['POST'])
@login_required
def update_status():
    if current_user.role == 'Conductor':
        current_user.current_status = request.form.get('status'); db.session.commit(); flash('Estado actualizado.', 'info')
    return redirect(url_for('dashboard'))

# --- ADMIN: CAMBIAR ESTADO DE OTROS (LA NOVEDAD) ---
@app.route('/admin/force_status_change/<int:driver_id>', methods=['POST'])
@login_required
def force_status_change(driver_id):
    if current_user.role != 'Supervisor': return "403", 403
    driver = User.query.get(driver_id)
    new_status = request.form.get('status')
    if driver and new_status:
        driver.current_status = new_status; db.session.commit()
        flash(f'Estado de {{driver.name}} cambiado a {{new_status}}', 'info')
    return redirect(url_for('dashboard'))

@app.route('/admin/next_turn', methods=['POST'])
@login_required
def next_turn():
    if current_user.role != 'Supervisor': return "403", 403
    settings = GlobalSettings.query.first()
    drivers = User.query.filter_by(role='Conductor').all()
    hoy = {{0: 'Lunes', 1: 'Martes', 2: 'Miércoles', 3: 'Jueves', 4: 'Viernes', 5: 'Sábado', 6: 'Domingo'}}[datetime.now().weekday()]
    candidatos = [d for d in drivers if d.current_status == 'Activo' and hoy not in d.fixed_days_off]
    if not candidatos: flash('Nadie disponible hoy.', 'danger')
    else:
        def get_date(x): return x.last_escoba_date if x.last_escoba_date else datetime(1900,1,1)
        candidatos.sort(key=lambda x: (get_date(x), x.id))
        elegido = candidatos[0]
        settings.current_escoba_name = elegido.name; settings.current_escoba2_name = None; settings.last_rotation_date = datetime.now()
        elegido.last_escoba_date = datetime.now(); db.session.commit()
        flash(f'Nuevo Turno: {{elegido.name}}', 'success')
    return redirect(url_for('dashboard'))

@app.route('/admin/add_extra_turn', methods=['POST'])
@login_required
def add_extra_turn():
    if current_user.role != 'Supervisor': return "403", 403
    settings = GlobalSettings.query.first()
    if settings.current_escoba2_name: flash('Ya hay refuerzo.', 'warning'); return redirect(url_for('dashboard'))
    drivers = User.query.filter_by(role='Conductor').all()
    hoy = {{0: 'Lunes', 1: 'Martes', 2: 'Miércoles', 3: 'Jueves', 4: 'Viernes', 5: 'Sábado', 6: 'Domingo'}}[datetime.now().weekday()]
    candidatos = [d for d in drivers if d.current_status == 'Activo' and hoy not in d.fixed_days_off and d.name != settings.current_escoba_name]
    if not candidatos: flash('No quedan conductores.', 'danger')
    else:
        def get_date(x): return x.last_escoba_date if x.last_escoba_date else datetime(1900,1,1)
        candidatos.sort(key=lambda x: (get_date(x), x.id))
        elegido = candidatos[0]
        settings.current_escoba2_name = elegido.name; elegido.last_escoba_date = datetime.now()
        db.session.commit(); flash(f'Refuerzo: {{elegido.name}}', 'success')
    return redirect(url_for('dashboard'))

@app.route('/admin/add_driver', methods=['POST'])
@login_required
def add_driver():
    if current_user.role != 'Supervisor': return "403", 403
    name = request.form.get('new_driver_name').strip().upper()
    if not name: return redirect(url_for('dashboard'))
    if User.query.filter_by(name=name).first(): flash('Ya existe.', 'warning')
    else:
        pin = str(random.randint(1000, 9999))
        db.session.add(User(name=name, role='Conductor', current_status='Baja Laboral', is_registered=False, signup_pin=pin))
        db.session.commit(); flash(f'Añadido: {{name}} (PIN: {{pin}})', 'success')
    return redirect(url_for('dashboard'))

@app.route('/admin/delete_driver/<int:driver_id>', methods=['POST'])
@login_required
def delete_driver(driver_id):
    if current_user.role != 'Supervisor': return "403", 403
    driver = User.query.get(driver_id)
    if driver and driver.role == 'Conductor':
        s = GlobalSettings.query.first()
        if driver.name == s.current_escoba_name or driver.name == s.current_escoba2_name: flash('No puedes borrar al escoba actual.', 'danger')
        else: db.session.delete(driver); db.session.commit(); flash(f'Eliminado: {{driver.name}}', 'success')
    return redirect(url_for('dashboard'))

@app.route('/logout')
@login_required
def logout(): logout_user(); return redirect(url_for('login'))

if __name__ == '__main__': app.run(debug=True)
"""

html_dashboard = f"""{{% extends "base.html" %}}
{{% block content %}}
<div class="card text-center mb-4 shadow-sm border-primary">
    <div class="card-header bg-primary text-white fw-bold">🧹 ESCOBA DEL DÍA ({{{{ hoy_dia }}}})</div>
    <div class="card-body">
        <h1 class="display-3 fw-bold text-dark">{{{{ escoba1 }}}}</h1>
        {{% if escoba2 %}}<div class="mt-2 p-2 bg-warning bg-opacity-25 border border-warning rounded"><span class="badge bg-warning text-dark mb-1">REFUERZO / 2º FURGONETA</span><h2 class="fw-bold text-dark">{{{{ escoba2 }}}}</h2></div>{{% endif %}}
        {{% if user.role == 'Supervisor' %}}
            <div class="mt-4 d-flex justify-content-center gap-2">
                <form action="/admin/next_turn" method="POST"><button type="submit" class="btn btn-danger btn-lg" onclick="return confirm('¿Rotar turno?')">🔄 CALCULAR SIGUIENTE</button></form>
                {{% if escoba1 != 'Ninguno' and not escoba2 %}}<form action="/admin/add_extra_turn" method="POST"><button type="submit" class="btn btn-outline-success btn-lg" onclick="return confirm('¿Añadir refuerzo?')">➕ AÑADIR REFUERZO</button></form>{{% endif %}}
            </div>
        {{% endif %}}
    </div>
</div>

{{% if user.role == 'Conductor' %}}<div class="card mb-4 shadow border-warning"><div class="card-body d-flex justify-content-between align-items-center"><div><h5 class="mb-1">{{{{ user.name }}}}</h5><small class="text-muted">Días Off: {{{{ user.fixed_days_off }}}}</small></div><form action="/update_status" method="POST"><select name="status" class="form-select fw-bold form-select-sm" onchange="this.form.submit()"><option value="Activo" {{% if user.current_status == 'Activo' %}}selected{{% endif %}}>🟢 Activo</option><option value="Vacaciones" {{% if user.current_status == 'Vacaciones' %}}selected{{% endif %}}>✈️ Vacaciones</option><option value="Baja Laboral" {{% if user.current_status == 'Baja Laboral' %}}selected{{% endif %}}>🚑 Baja</option><option value="Libre" {{% if user.current_status == 'Libre' %}}selected{{% endif %}}>🔵 Asuntos</option></select></form></div></div>{{% endif %}}

{{% if user.role == 'Supervisor' %}}
<div class="d-flex justify-content-between align-items-center mb-3">
    <h6 class="text-muted text-uppercase small fw-bold mb-0">Plantilla de Conductores</h6>
    <button class="btn btn-sm btn-primary" data-bs-toggle="modal" data-bs-target="#modalAddDriver">👤 Nuevo Conductor</button>
</div>
{{% else %}}<h6 class="text-muted text-uppercase small fw-bold mb-3">Cola de Rotación (Antigüedad)</h6>{{% endif %}}

<div class="row">
    {{% for d in drivers %}}
    <div class="col-12 col-md-6 mb-2">
        <div class="card h-100 {{% if d.name == escoba1 or d.name == escoba2 %}}border-success bg-light{{% endif %}}">
            <div class="card-body p-2 d-flex justify-content-between align-items-center">
                <div>
                    <div class="fw-bold">{{{{ d.name }}}}</div>
                    <div class="small text-muted">Última vez: {{% if d.last_escoba_date %}}<span class="text-dark fw-bold">{{{{ d.last_escoba_date.strftime('%d/%m') }}}}</span>{{% else %}}<span class="text-danger fw-bold">NUNCA</span>{{% endif %}}</div>
                </div>
                <div class="text-end d-flex align-items-center gap-2">
                    {{% if user.role == 'Supervisor' %}}
                        <form action="/admin/force_status_change/{{{{ d.id }}}}" method="POST">
                            <select name="status" class="form-select form-select-sm fw-bold border-0 {{% if d.current_status == 'Activo' %}}bg-success text-white{{% elif d.current_status == 'Baja Laboral' %}}bg-danger text-white{{% else %}}bg-warning text-dark{{% endif %}}" onchange="this.form.submit()" style="width: auto; cursor: pointer;">
                                <option value="Activo" {{% if d.current_status == 'Activo' %}}selected{{% endif %}}>🟢 Activo</option>
                                <option value="Vacaciones" {{% if d.current_status == 'Vacaciones' %}}selected{{% endif %}}>✈️ Vacaciones</option>
                                <option value="Baja Laboral" {{% if d.current_status == 'Baja Laboral' %}}selected{{% endif %}}>🚑 Baja</option>
                                <option value="Libre" {{% if d.current_status == 'Libre' %}}selected{{% endif %}}>🔵 Asuntos</option>
                            </select>
                        </form>
                    {{% else %}}
                        <span class="badge {{% if d.current_status == 'Activo' %}}bg-success{{% else %}}bg-secondary{{% endif %}}">{{{{ d.current_status }}}}</span>
                    {{% endif %}}

                    {{% if d.name == escoba1 %}}<span class="fs-1">🧹</span>{{% elif d.name == escoba2 %}}<span class="fs-1">🚐</span>{{% endif %}}
                    
                    {{% if user.role == 'Supervisor' %}}
                    <form action="/admin/delete_driver/{{{{ d.id }}}}" method="POST">
                        <button type="submit" class="btn btn-outline-danger btn-sm py-0 px-1" style="font-size: 0.7rem;" onclick="return confirm('¿Eliminar a {{{{ d.name }}}}?')">🗑️</button>
                    </form>
                    {{% endif %}}
                </div>
            </div>
        </div>
    </div>
    {{% endfor %}}
</div>

{{% if user.role == 'Supervisor' %}}
<div class="modal fade" id="modalAddDriver" tabindex="-1"><div class="modal-dialog modal-dialog-centered"><div class="modal-content"><div class="modal-header bg-primary text-white"><h5 class="modal-title">Contratar Nuevo Conductor</h5><button type="button" class="btn-close btn-close-white" data-bs-dismiss="modal"></button></div><div class="modal-body"><form action="/admin/add_driver" method="POST"><div class="mb-3"><label class="form-label">Nombre</label><input type="text" name="new_driver_name" class="form-control" required placeholder="Ej: PEDRO P."></div><button type="submit" class="btn btn-primary w-100">Crear</button></form></div></div></div></div>
<hr class="mt-5"><div class="accordion" id="accordionPin"><div class="accordion-item border-danger"><h2 class="accordion-header"><button class="accordion-button collapsed bg-danger text-white" type="button" data-bs-toggle="collapse" data-bs-target="#collapsePin">👮‍♂️ CÓDIGOS PIN</button></h2><div id="collapsePin" class="accordion-collapse collapse"><div class="accordion-body p-0"><table class="table table-striped table-sm mb-0 text-center small"><thead class="table-dark"><tr><th>Conductor</th><th>PIN</th><th>Acción</th></tr></thead><tbody>{{% for d in drivers %}}<tr><td class="text-start fw-bold ps-3">{{{{ d.name }}}}</td><td class="font-monospace text-danger fw-bold fs-5">{{{{ d.signup_pin }}}}</td><td>{{% if d.is_registered %}}<span class="badge bg-success">Registrado ✅</span>{{% else %}}<a href="https://wa.me/?text=Hola%20{{{{ d.name }}}},%20bienvenido%20a%20Escoba%20Drives.%20🚌%0A%0ATu%20PIN%20de%20seguridad%20es:%20*{{{{ d.signup_pin }}}}*%0A%0AEntra%20y%20regístrate%20aquí:%0Ahttps://Yoeph.pythonanywhere.com" target="_blank" class="btn btn-sm btn-success fw-bold">📲 Enviar PIN</a>{{% endif %}}</td></tr>{{% endfor %}}</tbody></table></div></div></div></div>{{% endif %}}
{{% endblock %}}"""

def main():
    # Escribir los archivos en la carpeta real
    with open(os.path.join(target_folder, 'app.py'), 'w', encoding='utf-8') as f:
        f.write(file_app_py)
    
    tpl_path = os.path.join(target_folder, 'templates', 'dashboard.html')
    with open(tpl_path, 'w', encoding='utf-8') as f:
        f.write(html_dashboard)
    
    print("✅ ¡ARCHIVOS SOBREESCRITOS CORRECTAMENTE!")
    print("   Git ahora detectará cambios 100% seguro.")

if __name__ == "__main__":
    main()