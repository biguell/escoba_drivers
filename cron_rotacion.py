# Importamos la 'app' y la base de datos 'db' desde tu archivo principal
from app import app, db, User, GlobalSettings
from datetime import datetime

def rotacion_automatica():
    # Esto es necesario para que el script pueda 'entrar' en la base de datos de Flask
    with app.app_context():
        print(f"--- 🤖 INICIO AUTOMATIZACIÓN: {datetime.now()} ---")
        
        settings = GlobalSettings.query.first()
        drivers = User.query.filter_by(role='Conductor').all()
        
        # Mapeo de días
        dias_map = {0: 'Lunes', 1: 'Martes', 2: 'Miércoles', 3: 'Jueves', 4: 'Viernes', 5: 'Sábado', 6: 'Domingo'}
        hoy_num = datetime.now().weekday()
        hoy_nombre = dias_map[hoy_num]
        
        print(f"Calculando turno para: {hoy_nombre}")

        candidatos = []
        for d in drivers:
            # 1. Filtro Estado
            if d.current_status != 'Activo':
                print(f"❌ {d.name}: No está Activo ({d.current_status})")
                continue
            # 2. Filtro Día Libre
            if hoy_nombre in d.fixed_days_off:
                print(f"⛔ {d.name}: Libra hoy ({d.fixed_days_off})")
                continue
            candidatos.append(d)

        if not candidatos:
            print("⚠️ ALERTA: Nadie disponible hoy.")
        else:
            # 3. Ordenar por antigüedad (Justicia Histórica)
            def get_date(x): return x.last_escoba_date if x.last_escoba_date else datetime(1900,1,1)
            candidatos.sort(key=lambda x: (get_date(x), x.id))
            
            elegido = candidatos[0]
            
            # Guardar cambios
            settings.current_escoba_name = elegido.name
            settings.last_rotation_date = datetime.now()
            elegido.last_escoba_date = datetime.now()
            
            db.session.commit()
            print(f"✅ NUEVO ESCOBA ASIGNADO: {elegido.name}")

if __name__ == "__main__":
    rotacion_automatica()