from flask_sqlalchemy import SQLAlchemy
from datetime import datetime

db = SQLAlchemy()

def init_db(app):
    """Inicializa la base de datos"""
    from models import MenuItem  # import inside to avoid circular import
    db.init_app(app)
    with app.app_context():
        db.create_all()
        # Insertar datos iniciales si la DB está vacía
        if MenuItem.query.count() == 0:
            seed_menu()

def seed_menu():
    """Inserta datos iniciales en el menú"""
    from models import MenuItem
    initial_items = [
        MenuItem(name='Tacos al Pastor', price=45.00, category='Tacos', available=True),
        MenuItem(name='Quesadillas', price=55.00, category='Antojitos', available=True),
        MenuItem(name='Enchiladas Verdes', price=85.00, category='Platos Fuertes', available=True),
        MenuItem(name='Pozole Rojo', price=95.00, category='Platos Fuertes', available=True),
        MenuItem(name='Chilaquiles', price=65.00, category='Desayunos', available=True),
        MenuItem(name='Agua de Horchata', price=25.00, category='Bebidas', available=True),
        MenuItem(name='Guacamole', price=45.00, category='Entradas', available=True),
        MenuItem(name='Flan Napolitano', price=40.00, category='Postres', available=True),
    ]
    
    for item in initial_items:
        db.session.add(item)
    
    db.session.commit()
