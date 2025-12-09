from datetime import date, datetime
from decimal import Decimal, ROUND_HALF_UP

from flask import Blueprint, jsonify, request, send_file
from sqlalchemy import func

from auth_utils import role_required
from database import db
from models import DailySales, MenuItem, Order, OrderItem
from utils.ticket_generator import TicketGenerator

order_bp = Blueprint("order_bp", __name__)
_ticket_generator = TicketGenerator()


def _quantize(value: Decimal) -> Decimal:
    return value.quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)


def _update_daily_sales(order: Order) -> None:
    """Actualiza el resumen de ventas diarias."""
    today = date.today()
    daily_sales = DailySales.query.filter_by(date=today).first()

    if not daily_sales:
        daily_sales = DailySales(
            date=today,
            total_orders=0,
            total_sales=0.0,
            total_iva=0.0,
            cash_sales=0.0,
            card_sales=0.0,
        )
        db.session.add(daily_sales)

    daily_sales.total_orders += 1
    daily_sales.total_sales += order.total
    daily_sales.total_iva += order.iva

    if order.payment_method == "cash":
        daily_sales.cash_sales += order.total
    elif order.payment_method == "card":
        daily_sales.card_sales += order.total


@order_bp.route("/", methods=["POST"])
@role_required("admin", "cashier")
def create_order():
    """Crea una nueva orden."""
    data = request.get_json() or {}

    items_payload = data.get("items", [])
    if not items_payload:
        return jsonify({"error": "Se requieren items para crear la orden"}), 400

    payment_method = data.get("payment_method", "cash")

    subtotal_dec = Decimal("0.00")
    order_items: list[OrderItem] = []

    # Calcular totales en servidor para evitar manipulación
    for item_data in items_payload:
        menu_item = MenuItem.query.get(item_data.get("id"))
        if not menu_item or not menu_item.available:
            return jsonify({"error": "Producto no disponible"}), 400

        quantity = int(item_data.get("quantity", 1))
        unit_price = Decimal(str(menu_item.price))
        line_total = _quantize(unit_price * quantity)
        subtotal_dec += line_total

        order_item = OrderItem(
            menu_item_id=menu_item.id,
            quantity=quantity,
            unit_price=float(unit_price),
            subtotal=float(line_total),
            notes=item_data.get("notes"),
        )
        order_items.append(order_item)

    iva_dec = _quantize(subtotal_dec * Decimal("0.16"))
    total_dec = _quantize(subtotal_dec + iva_dec)

    # Obtener el último número de ticket de forma segura
    last_order = Order.query.order_by(Order.ticket_number.desc()).first()
    new_ticket_number = (last_order.ticket_number + 1) if last_order else 1

    new_order = Order(
        ticket_number=new_ticket_number,
        customer_name=data.get("customer_name", "Cliente General"),
        subtotal=float(subtotal_dec),
        iva=float(iva_dec),
        total=float(total_dec),
        payment_method=payment_method,
        status="completed",
        printed=False,
    )

    db.session.add(new_order)
    db.session.flush()

    for order_item in order_items:
        order_item.order_id = new_order.id
        db.session.add(order_item)

    _update_daily_sales(new_order)
    db.session.commit()

    return jsonify(new_order.to_dict()), 201


@order_bp.route("/", methods=["GET"])
@role_required("admin", "cashier")
def get_orders():
    """
    Obtiene todas las órdenes con filtros opcionales:
    - ?date=YYYY-MM-DD
    - ?status=pending|completed|cancelled
    """
    date_filter = request.args.get("date")
    status = request.args.get("status")

    query = Order.query

    if date_filter:
        target_date = datetime.strptime(date_filter, "%Y-%m-%d").date()
        query = query.filter(func.date(Order.created_at) == target_date)

    if status:
        query = query.filter_by(status=status)

    orders = query.order_by(Order.created_at.desc()).all()
    return jsonify([order.to_dict() for order in orders])


@order_bp.route("/<int:order_id>", methods=["GET"])
@role_required("admin", "cashier")
def get_order(order_id):
    """Obtiene una orden específica."""
    order = Order.query.get_or_404(order_id)
    return jsonify(order.to_dict())


@order_bp.route("/<int:order_id>/cancel", methods=["PUT"])
@role_required("admin")
def cancel_order(order_id):
    """Cancela una orden."""
    order = Order.query.get_or_404(order_id)
    order.status = "cancelled"
    db.session.commit()
    return jsonify(order.to_dict())


@order_bp.route("/<int:order_id>/ticket", methods=["GET"])
@role_required("admin", "cashier")
def download_ticket(order_id):
    """Genera y descarga el ticket PDF de una orden."""
    order = Order.query.get_or_404(order_id)
    order_data = {
        "ticket_number": order.ticket_number,
        "customer_name": order.customer_name,
        "items": [
            {
                "name": item.menu_item.name,
                "quantity": item.quantity,
                "price": item.unit_price,
            }
            for item in order.items
        ],
        "subtotal": order.subtotal,
        "iva": order.iva,
        "total": order.total,
    }

    filepath = _ticket_generator.generate_ticket(order_data)
    order.printed = True
    db.session.commit()

    return send_file(
        filepath,
        mimetype="application/pdf",
        as_attachment=True,
        download_name=f"ticket_{order.ticket_number:04d}.pdf",
    )
