import os

from flask_sqlalchemy import SQLAlchemy

db = SQLAlchemy()


def init_db(app):
    """
    Inicializa la base de datos y crea tablas.
    Si la tabla de menú está vacía, inserta datos de ejemplo.
    """
    from models import MenuItem, User  # Import local para evitar import circular

    db.init_app(app)

    with app.app_context():
        db.create_all()

        if MenuItem.query.count() == 0:
            seed_menu()

        if User.query.count() == 0:
            seed_admin(User)


def seed_menu():
    """Inserta datos iniciales en el menú."""
    from models import MenuItem

    initial_items = [
        MenuItem(name="Tacos al Pastor", price=45.00, category="Tacos", available=True),
        MenuItem(name="Quesadillas", price=55.00, category="Antojitos", available=True),
        MenuItem(
            name="Enchiladas Verdes",
            price=85.00,
            category="Platos Fuertes",
            available=True,
        ),
        MenuItem(
            name="Pozole Rojo",
            price=95.00,
            category="Platos Fuertes",
            available=True,
        ),
        MenuItem(name="Chilaquiles", price=65.00, category="Desayunos", available=True),
        MenuItem(name="Agua de Horchata", price=25.00, category="Bebidas", available=True),
        MenuItem(name="Guacamole", price=45.00, category="Entradas", available=True),
        MenuItem(
            name="Flan Napolitano", price=40.00, category="Postres", available=True
        ),
    ]

    db.session.add_all(initial_items)
    db.session.commit()


def seed_admin(User):
    """Crea un usuario administrador por defecto si no existen usuarios."""
    admin_username = os.getenv("ADMIN_USERNAME", "admin")
    admin_password = os.getenv("ADMIN_PASSWORD", "admin123")

    admin_user = User(username=admin_username, role="admin")
    admin_user.set_password(admin_password)
    db.session.add(admin_user)
    db.session.commit()
