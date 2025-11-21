from app import app, db, User, GlobalSettings
from datetime import datetime

def rotacion_automatica():
    with app.app_context():
        print(f"--- 🤖 ROBOT V4: INICIO AUTOMATIZACIÓN {datetime.now()} ---")
        
        settings = GlobalSettings.query.first()
        drivers = User.query.filter_by(role='Conductor').all()
        
        dias_map = {0: 'Lunes', 1: 'Martes', 2: 'Miércoles', 3: 'Jueves', 4: 'Viernes', 5: 'Sábado', 6: 'Domingo'}
        hoy_num = datetime.now().weekday()
        hoy_nombre = dias_map[hoy_num]
        
        print(f"Calculando turno para: {hoy_nombre}")

        candidatos = []
        for d in drivers:
            if d.current_status != 'Activo':
                continue
            if hoy_nombre in d.fixed_days_off:
                continue
            candidatos.append(d)

        if not candidatos:
            print("⚠️ ALERTA: Nadie disponible hoy.")
        else:
            # Ordenar por antigüedad
            def get_date(x): return x.last_escoba_date if x.last_escoba_date else datetime(1900,1,1)
            candidatos.sort(key=lambda x: (get_date(x), x.id))
            
            elegido = candidatos[0]
            
            # ASIGNAR NUEVO Y LIMPIAR EL VIEJO
            settings.current_escoba_name = elegido.name
            settings.current_escoba2_name = None  # <--- ¡IMPORTANTE! Limpiamos el refuerzo
            
            settings.last_rotation_date = datetime.now()
            elegido.last_escoba_date = datetime.now()
            
            db.session.commit()
            print(f"✅ NUEVO ESCOBA: {elegido.name} (Refuerzo limpiado)")

if __name__ == "__main__":
    rotacion_automatica()