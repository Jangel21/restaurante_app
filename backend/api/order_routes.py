from datetime import date, datetime
from decimal import Decimal, ROUND_HALF_UP

from flask import Blueprint, jsonify, request, send_file
from sqlalchemy import func

from auth_utils import role_required, get_current_user_id
from database import db
from models import DailySales, MenuItem, Order, OrderItem
from utils.ticket_generator import TicketGenerator

order_bp = Blueprint("order_bp", __name__)
_ticket_generator = TicketGenerator()


def _quantize(value: Decimal) -> Decimal:
    return value.quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)


def _recalculate_order_totals(order: Order) -> None:
    """Recalcula los totales de una orden basándose en sus items."""
    subtotal_dec = Decimal("0.00")
    
    for item in order.items:
        subtotal_dec += Decimal(str(item.subtotal))
    
    iva_dec = _quantize(subtotal_dec * Decimal("0.16"))
    total_dec = _quantize(subtotal_dec + iva_dec)
    
    order.subtotal = float(subtotal_dec)
    order.iva = float(iva_dec)
    order.total = float(total_dec)


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
@role_required("admin", "cashier", "waiter")
def create_order():
    """
    Crea una nueva orden (ticket abierto por defecto).
    Los meseros y cajeros pueden crear órdenes abiertas.
    ---
    tags:
      - orders
    consumes:
      - application/json
    parameters:
      - in: body
        name: body
        schema:
          type: object
          properties:
            customer_name:
              type: string
            order_type:
              type: string
              enum: [local, takeout, delivery]
            delivery_phone:
              type: string
            delivery_address:
              type: string
            payment_method:
              type: string
              enum: [cash, card]
            items:
              type: array
              items:
                type: object
                required: [id, quantity]
                properties:
                  id:
                    type: integer
                  quantity:
                    type: integer
                  notes:
                    type: string
    security:
      - BearerAuth: []
    responses:
      201:
        description: Orden creada
      400:
        description: Datos inválidos
      403:
        description: No autorizado
    """
    data = request.get_json() or {}
    user_id = get_current_user_id()

    # Validación de tipo de orden
    order_type = data.get("order_type", "local")  # local|takeout|delivery
    
    if order_type not in ["local", "takeout", "delivery"]:
        return jsonify({"error": "Tipo de orden inválido"}), 400
    
    # Si es delivery, requerir datos
    if order_type == "delivery":
        if not data.get("delivery_phone") or not data.get("delivery_address"):
            return jsonify({"error": "Para órdenes a domicilio se requiere teléfono y dirección"}), 400

    # Obtener el último número de ticket
    last_order = Order.query.order_by(Order.ticket_number.desc()).first()
    new_ticket_number = (last_order.ticket_number + 1) if last_order else 1

    # Crear orden con status "open"
    new_order = Order(
        ticket_number=new_ticket_number,
        customer_name=data.get("customer_name", "Cliente General"),
        order_type=order_type,
        delivery_phone=data.get("delivery_phone"),
        delivery_address=data.get("delivery_address"),
        subtotal=0.0,
        iva=0.0,
        total=0.0,
        payment_method=data.get("payment_method", "cash"),
        status="open",
        created_by_user_id=user_id,
        printed=False,
    )

    db.session.add(new_order)
    db.session.flush()

    # Agregar items iniciales si se proporcionan
    items_payload = data.get("items", [])
    if items_payload:
        for item_data in items_payload:
            menu_item = MenuItem.query.get(item_data.get("id"))
            if not menu_item or not menu_item.available:
                db.session.rollback()
                return jsonify({"error": f"Producto {item_data.get('id')} no disponible"}), 400

            quantity = int(item_data.get("quantity", 1))
            unit_price = Decimal(str(menu_item.price))
            line_total = _quantize(unit_price * quantity)

            order_item = OrderItem(
                order_id=new_order.id,
                menu_item_id=menu_item.id,
                quantity=quantity,
                unit_price=float(unit_price),
                subtotal=float(line_total),
                notes=item_data.get("notes"),
            )
            db.session.add(order_item)

        # Recalcular totales
        db.session.flush()
        _recalculate_order_totals(new_order)

    db.session.commit()
    return jsonify(new_order.to_dict()), 201


@order_bp.route("/<int:order_id>/items", methods=["POST"])
@role_required("admin", "cashier", "waiter")
def add_items_to_order(order_id):
    """
    Agrega items a un ticket abierto.
    Solo se pueden agregar items a tickets con status 'open'.
    ---
    tags:
      - orders
    parameters:
      - in: path
        name: order_id
        type: integer
        required: true
      - in: body
        name: body
        schema:
          type: object
          properties:
            items:
              type: array
              items:
                type: object
                required: [id, quantity]
                properties:
                  id: {type: integer}
                  quantity: {type: integer}
                  notes: {type: string}
    security:
      - BearerAuth: []
    responses:
      200:
        description: Orden actualizada
      400:
        description: Datos inválidos
      404:
        description: Orden no encontrada
    """
    order = Order.query.get_or_404(order_id)
    
    if order.status != "open":
        return jsonify({"error": "Solo se pueden agregar items a tickets abiertos"}), 400

    data = request.get_json() or {}
    items_payload = data.get("items", [])
    
    if not items_payload:
        return jsonify({"error": "Se requieren items para agregar"}), 400

    # Agregar nuevos items
    for item_data in items_payload:
        menu_item = MenuItem.query.get(item_data.get("id"))
        if not menu_item or not menu_item.available:
            return jsonify({"error": f"Producto {item_data.get('id')} no disponible"}), 400

        quantity = int(item_data.get("quantity", 1))
        unit_price = Decimal(str(menu_item.price))
        line_total = _quantize(unit_price * quantity)

        order_item = OrderItem(
            order_id=order.id,
            menu_item_id=menu_item.id,
            quantity=quantity,
            unit_price=float(unit_price),
            subtotal=float(line_total),
            notes=item_data.get("notes"),
        )
        db.session.add(order_item)

    db.session.flush()
    _recalculate_order_totals(order)
    db.session.commit()

    return jsonify(order.to_dict())


@order_bp.route("/<int:order_id>/items/<int:item_id>", methods=["DELETE"])
@role_required("admin", "cashier", "waiter")
def remove_item_from_order(order_id, item_id):
    """
    Elimina un item de un ticket abierto.
    ---
    tags:
      - orders
    parameters:
      - in: path
        name: order_id
        type: integer
        required: true
      - in: path
        name: item_id
        type: integer
        required: true
    security:
      - BearerAuth: []
    responses:
      200:
        description: Item eliminado
      400:
        description: Solo tickets abiertos
      404:
        description: Orden o item no encontrado
    """
    order = Order.query.get_or_404(order_id)
    
    if order.status != "open":
        return jsonify({"error": "Solo se pueden eliminar items de tickets abiertos"}), 400

    order_item = OrderItem.query.filter_by(id=item_id, order_id=order_id).first_or_404()
    
    db.session.delete(order_item)
    db.session.flush()
    
    _recalculate_order_totals(order)
    db.session.commit()

    return jsonify(order.to_dict())


@order_bp.route("/<int:order_id>/items/<int:item_id>", methods=["PUT"])
@role_required("admin", "cashier", "waiter")
def update_order_item(order_id, item_id):
    """
    Actualiza un item de un ticket abierto (cantidad o notas).
    ---
    tags:
      - orders
    parameters:
      - in: path
        name: order_id
        type: integer
        required: true
      - in: path
        name: item_id
        type: integer
        required: true
      - in: body
        name: body
        schema:
          type: object
          properties:
            quantity: {type: integer}
            notes: {type: string}
    security:
      - BearerAuth: []
    responses:
      200:
        description: Item actualizado
      400:
        description: Datos inválidos
      404:
        description: Orden o item no encontrado
    """
    order = Order.query.get_or_404(order_id)
    
    if order.status != "open":
        return jsonify({"error": "Solo se pueden modificar items de tickets abiertos"}), 400

    order_item = OrderItem.query.filter_by(id=item_id, order_id=order_id).first_or_404()
    
    data = request.get_json() or {}
    
    if "quantity" in data:
        new_quantity = int(data["quantity"])
        if new_quantity <= 0:
            return jsonify({"error": "La cantidad debe ser mayor a 0"}), 400
        
        order_item.quantity = new_quantity
        order_item.subtotal = float(_quantize(Decimal(str(order_item.unit_price)) * new_quantity))
    
    if "notes" in data:
        order_item.notes = data["notes"]
    
    db.session.flush()
    _recalculate_order_totals(order)
    db.session.commit()

    return jsonify(order.to_dict())


@order_bp.route("/<int:order_id>/complete", methods=["PUT"])
@role_required("admin", "cashier")
def complete_order(order_id):
    """
    Completa un ticket abierto (cierra la orden).
    Solo cajeros y admins pueden completar órdenes.
    ---
    tags:
      - orders
    parameters:
      - in: path
        name: order_id
        type: integer
        required: true
      - in: body
        name: body
        schema:
          type: object
          properties:
            payment_method:
              type: string
              enum: [cash, card]
    security:
      - BearerAuth: []
    responses:
      200:
        description: Orden completada
      400:
        description: Solo tickets abiertos
      404:
        description: Orden no encontrada
    """
    order = Order.query.get_or_404(order_id)
    
    if order.status != "open":
        return jsonify({"error": "Solo se pueden completar tickets abiertos"}), 400

    data = request.get_json() or {}
    
    # Actualizar método de pago si se proporciona
    if "payment_method" in data:
        order.payment_method = data["payment_method"]

    order.status = "completed"
    order.completed_at = datetime.utcnow()
    
    # Actualizar ventas diarias
    _update_daily_sales(order)
    
    db.session.commit()
    return jsonify(order.to_dict())


@order_bp.route("/", methods=["GET"])
@role_required("admin", "cashier", "waiter")
def get_orders():
    """
    Obtiene todas las órdenes con filtros opcionales:
    - ?date=YYYY-MM-DD
    - ?status=open|completed|cancelled
    - ?order_type=local|takeout|delivery
    ---
    tags:
      - orders
    parameters:
      - in: query
        name: date
        type: string
      - in: query
        name: status
        type: string
      - in: query
        name: order_type
        type: string
    security:
      - BearerAuth: []
    responses:
      200:
        description: Lista de órdenes
    """
    date_filter = request.args.get("date")
    status = request.args.get("status")
    order_type = request.args.get("order_type")

    query = Order.query

    if date_filter:
        target_date = datetime.strptime(date_filter, "%Y-%m-%d").date()
        query = query.filter(func.date(Order.created_at) == target_date)

    if status:
        query = query.filter_by(status=status)
    
    if order_type:
        query = query.filter_by(order_type=order_type)

    orders = query.order_by(Order.created_at.desc()).all()
    return jsonify([order.to_dict() for order in orders])


@order_bp.route("/open", methods=["GET"])
@role_required("admin", "cashier", "waiter")
def get_open_orders():
    """
    Obtiene todos los tickets abiertos.
    ---
    tags:
      - orders
    security:
      - BearerAuth: []
    responses:
      200:
        description: Lista de órdenes abiertas
    """
    orders = Order.query.filter_by(status="open").order_by(Order.created_at.desc()).all()
    return jsonify([order.to_dict() for order in orders])


@order_bp.route("/<int:order_id>", methods=["GET"])
@role_required("admin", "cashier", "waiter")
def get_order(order_id):
    """
    Obtiene una orden específica.
    ---
    tags:
      - orders
    parameters:
      - in: path
        name: order_id
        type: integer
        required: true
    security:
      - BearerAuth: []
    responses:
      200:
        description: Orden
      404:
        description: No encontrada
    """
    order = Order.query.get_or_404(order_id)
    return jsonify(order.to_dict())


@order_bp.route("/<int:order_id>/cancel", methods=["PUT"])
@role_required("admin", "cashier")
def cancel_order(order_id):
    """
    Cancela una orden. Solo admins y cajeros pueden cancelar.
    ---
    tags:
      - orders
    parameters:
      - in: path
        name: order_id
        type: integer
        required: true
    security:
      - BearerAuth: []
    responses:
      200:
        description: Orden cancelada
      404:
        description: No encontrada
    """
    order = Order.query.get_or_404(order_id)
    order.status = "cancelled"
    db.session.commit()
    return jsonify(order.to_dict())


@order_bp.route("/<int:order_id>/ticket", methods=["GET"])
@role_required("admin", "cashier")
def download_ticket(order_id):
    """
    Genera y descarga el ticket PDF de una orden.
    ---
    tags:
      - orders
    produces:
      - application/pdf
    parameters:
      - in: path
        name: order_id
        type: integer
        required: true
    security:
      - BearerAuth: []
    responses:
      200:
        description: Ticket PDF
      404:
        description: Orden no encontrada
    """
    order = Order.query.get_or_404(order_id)
    
    order_data = {
        "ticket_number": order.ticket_number,
        "customer_name": order.customer_name,
        "order_type": order.order_type,
        "delivery_phone": order.delivery_phone,
        "delivery_address": order.delivery_address,
        "items": [
            {
                "name": item.menu_item.name,
                "quantity": item.quantity,
                "price": item.unit_price,
                "notes": item.notes,
            }
            for item in order.items
        ],
        "subtotal": order.subtotal,
        "iva": order.iva,
        "total": order.total,
        "payment_method": order.payment_method,
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
