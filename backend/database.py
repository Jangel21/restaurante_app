import os

from flask_sqlalchemy import SQLAlchemy

db = SQLAlchemy()


def init_db(app):
    """
    Inicializa la base de datos y crea tablas.
    Si la tabla de menú está vacía, inserta datos de ejemplo.
    """
    from models import MenuItem, User  # Import local para evitar import circular

    with app.app_context():
        db.create_all()

        if MenuItem.query.count() == 0:
            seed_menu()

        if User.query.count() == 0:
            seed_users()


def seed_menu():
    """Inserta datos iniciales en el menú."""
    from models import MenuItem

    initial_items = [
        MenuItem(name="Tacos al Pastor", price=45.00, category="Tacos", available=True),
        MenuItem(name="Tacos de Asada", price=45.00, category="Tacos", available=True),
        MenuItem(name="Tacos de Carnitas", price=45.00, category="Tacos", available=True),
        MenuItem(name="Quesadillas", price=55.00, category="Antojitos", available=True),
        MenuItem(name="Sopes", price=50.00, category="Antojitos", available=True),
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
        MenuItem(name="Molletes", price=55.00, category="Desayunos", available=True),
        MenuItem(name="Agua de Horchata", price=25.00, category="Bebidas", available=True),
        MenuItem(name="Agua de Jamaica", price=25.00, category="Bebidas", available=True),
        MenuItem(name="Refresco", price=30.00, category="Bebidas", available=True),
        MenuItem(name="Guacamole", price=45.00, category="Entradas", available=True),
        MenuItem(name="Nachos", price=65.00, category="Entradas", available=True),
        MenuItem(
            name="Flan Napolitano", price=40.00, category="Postres", available=True
        ),
        MenuItem(
            name="Pastel Tres Leches", price=45.00, category="Postres", available=True
        ),
    ]

    db.session.add_all(initial_items)
    db.session.commit()


def seed_users():
    """Crea usuarios por defecto."""
    from models import User

    # Usuario admin (caja/gerente)
    admin = User(
        username=os.getenv("ADMIN_USERNAME", "admin"),
        full_name="Administrador",
        role="admin"
    )
    admin.set_password(os.getenv("ADMIN_PASSWORD", "admin123"))

    # Usuario cajero
    cashier = User(
        username="cajero1",
        full_name="María González",
        role="cashier"
    )
    cashier.set_password("cajero123")

    # Usuario mesero
    waiter = User(
        username="mesero1",
        full_name="Juan Pérez",
        role="waiter"
    )
    waiter.set_password("mesero123")

    db.session.add_all([admin, cashier, waiter])
    db.session.commit()