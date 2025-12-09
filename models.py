from datetime import datetime

from database import db
from werkzeug.security import check_password_hash, generate_password_hash


class MenuItem(db.Model):
    """Modelo para items del menú."""
    __tablename__ = "menu_items"

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    price = db.Column(db.Float, nullable=False)
    category = db.Column(db.String(50), nullable=False)
    description = db.Column(db.Text)
    available = db.Column(db.Boolean, default=True)
    image_url = db.Column(db.String(255))

    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(
        db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow
    )

    def to_dict(self):
        return {
            "id": self.id,
            "name": self.name,
            "price": float(self.price),
            "category": self.category,
            "description": self.description,
            "available": self.available,
            "image_url": self.image_url,
        }


class Order(db.Model):
    """Modelo para órdenes."""
    __tablename__ = "orders"

    id = db.Column(db.Integer, primary_key=True)
    ticket_number = db.Column(db.Integer, unique=True, nullable=False)
    customer_name = db.Column(db.String(100), default="Cliente General")

    # Nuevos campos para tipo de orden
    order_type = db.Column(db.String(20), default="local")  # local|takeout|delivery
    delivery_phone = db.Column(db.String(20))
    delivery_address = db.Column(db.Text)

    subtotal = db.Column(db.Float, nullable=False, default=0.0)
    iva = db.Column(db.Float, nullable=False, default=0.0)
    total = db.Column(db.Float, nullable=False, default=0.0)

    # Cambio: ahora status puede ser 'open' (ticket abierto)
    status = db.Column(db.String(20), default="open")  # open|completed|cancelled
    payment_method = db.Column(db.String(20), default="cash")  # cash|card|transfer
    printed = db.Column(db.Boolean, default=False)

    # Usuario que creó la orden (mesero/cajero)
    created_by_user_id = db.Column(db.Integer, db.ForeignKey("users.id"))
    created_by = db.relationship("User", backref="orders_created")

    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    completed_at = db.Column(db.DateTime)

    # Relación con items de la orden
    items = db.relationship(
        "OrderItem",
        backref="order",
        lazy=True,
        cascade="all, delete-orphan",
    )

    def to_dict(self):
        return {
            "id": self.id,
            "ticket_number": self.ticket_number,
            "customer_name": self.customer_name,
            "order_type": self.order_type,
            "delivery_phone": self.delivery_phone,
            "delivery_address": self.delivery_address,
            "subtotal": float(self.subtotal),
            "iva": float(self.iva),
            "total": float(self.total),
            "status": self.status,
            "payment_method": self.payment_method,
            "printed": self.printed,
            "created_by": self.created_by.to_dict() if self.created_by else None,
            "created_at": self.created_at.isoformat(),
            "completed_at": self.completed_at.isoformat() if self.completed_at else None,
            "items": [item.to_dict() for item in self.items],
        }


class OrderItem(db.Model):
    """Modelo para items individuales de una orden."""
    __tablename__ = "order_items"

    id = db.Column(db.Integer, primary_key=True)

    order_id = db.Column(db.Integer, db.ForeignKey("orders.id"), nullable=False)
    menu_item_id = db.Column(db.Integer, db.ForeignKey("menu_items.id"), nullable=False)

    quantity = db.Column(db.Integer, nullable=False)
    unit_price = db.Column(db.Float, nullable=False)
    subtotal = db.Column(db.Float, nullable=False)
    notes = db.Column(db.Text)

    # Relación con el menu item
    menu_item = db.relationship("MenuItem", backref="order_items")

    def to_dict(self):
        return {
            "id": self.id,
            "menu_item": self.menu_item.to_dict(),
            "quantity": self.quantity,
            "unit_price": float(self.unit_price),
            "subtotal": float(self.subtotal),
            "notes": self.notes,
        }


class DailySales(db.Model):
    """Modelo para resumen de ventas diarias."""
    __tablename__ = "daily_sales"

    id = db.Column(db.Integer, primary_key=True)
    date = db.Column(db.Date, unique=True, nullable=False)

    total_orders = db.Column(db.Integer, default=0)
    total_sales = db.Column(db.Float, default=0.0)
    total_iva = db.Column(db.Float, default=0.0)
    cash_sales = db.Column(db.Float, default=0.0)
    card_sales = db.Column(db.Float, default=0.0)

    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    def to_dict(self):
        return {
            "id": self.id,
            "date": self.date.isoformat(),
            "total_orders": self.total_orders,
            "total_sales": float(self.total_sales),
            "total_iva": float(self.total_iva),
            "cash_sales": float(self.cash_sales),
            "card_sales": float(self.card_sales),
        }


class User(db.Model):
    """Modelo de usuarios para autenticación y roles."""

    __tablename__ = "users"

    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    password_hash = db.Column(db.String(255), nullable=False)
    full_name = db.Column(db.String(120))
    # Roles: admin (caja/gerente), cashier (cajero), waiter (mesero)
    role = db.Column(db.String(20), default="waiter")
    active = db.Column(db.Boolean, default=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    def set_password(self, password: str) -> None:
        self.password_hash = generate_password_hash(password)

    def check_password(self, password: str) -> bool:
        return check_password_hash(self.password_hash, password)

    def to_dict(self):
        return {
            "id": self.id,
            "username": self.username,
            "full_name": self.full_name,
            "role": self.role,
            "active": self.active,
        }