from flask import Flask, jsonify, request
from flask_cors import CORS
from database import db, init_db
from models import MenuItem, Order, OrderItem, DailySales
from datetime import datetime, date, timedelta
import os

app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///restaurant.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['SECRET_KEY'] = 'tu-clave-secreta-aqui'

# Habilitar CORS para desarrollo
CORS(app)

# Inicializar base de datos
init_db(app)

# ============= RUTAS DEL MENÚ =============

@app.route('/api/menu', methods=['GET'])
def get_menu():
    """Obtiene todos los items del menú"""
    category = request.args.get('category')
    
    if category and category != 'Todos':
        items = MenuItem.query.filter_by(category=category, available=True).all()
    else:
        items = MenuItem.query.filter_by(available=True).all()
    
    return jsonify([item.to_dict() for item in items])


@app.route('/api/menu/<int:item_id>', methods=['GET'])
def get_menu_item(item_id):
    """Obtiene un item específico del menú"""
    item = MenuItem.query.get_or_404(item_id)
    return jsonify(item.to_dict())


@app.route('/api/menu', methods=['POST'])
def create_menu_item():
    """Crea un nuevo item en el menú"""
    data = request.get_json()
    
    new_item = MenuItem(
        name=data['name'],
        price=data['price'],
        category=data['category'],
        description=data.get('description'),
        available=data.get('available', True),
        image_url=data.get('image_url')
    )
    
    db.session.add(new_item)
    db.session.commit()
    
    return jsonify(new_item.to_dict()), 201


@app.route('/api/menu/<int:item_id>', methods=['PUT'])
def update_menu_item(item_id):
    """Actualiza un item del menú"""
    item = MenuItem.query.get_or_404(item_id)
    data = request.get_json()
    
    item.name = data.get('name', item.name)
    item.price = data.get('price', item.price)
    item.category = data.get('category', item.category)
    item.description = data.get('description', item.description)
    item.available = data.get('available', item.available)
    item.image_url = data.get('image_url', item.image_url)
    
    db.session.commit()
    
    return jsonify(item.to_dict())


@app.route('/api/menu/<int:item_id>', methods=['DELETE'])
def delete_menu_item(item_id):
    """Elimina un item del menú"""
    item = MenuItem.query.get_or_404(item_id)
    db.session.delete(item)
    db.session.commit()
    
    return jsonify({'message': 'Item eliminado correctamente'}), 200


@app.route('/api/categories', methods=['GET'])
def get_categories():
    """Obtiene todas las categorías disponibles"""
    categories = db.session.query(MenuItem.category).distinct().all()
    return jsonify([cat[0] for cat in categories])


# ============= RUTAS DE ÓRDENES =============

@app.route('/api/orders', methods=['POST'])
def create_order():
    """Crea una nueva orden"""
    data = request.get_json()
    
    # Obtener el último número de ticket
    last_order = Order.query.order_by(Order.ticket_number.desc()).first()
    new_ticket_number = (last_order.ticket_number + 1) if last_order else 1
    
    # Crear la orden
    new_order = Order(
        ticket_number=new_ticket_number,
        customer_name=data.get('customer_name', 'Cliente General'),
        subtotal=data['subtotal'],
        iva=data['iva'],
        total=data['total'],
        payment_method=data.get('payment_method', 'cash'),
        status='completed'
    )
    
    db.session.add(new_order)
    db.session.flush()  # Para obtener el ID de la orden
    
    # Agregar items de la orden
    for item_data in data['items']:
        order_item = OrderItem(
            order_id=new_order.id,
            menu_item_id=item_data['id'],
            quantity=item_data['quantity'],
            unit_price=item_data['price'],
            subtotal=item_data['price'] * item_data['quantity'],
            notes=item_data.get('notes')
        )
        db.session.add(order_item)
    
    # Actualizar ventas diarias
    update_daily_sales(new_order)
    
    db.session.commit()
    
    return jsonify(new_order.to_dict()), 201


@app.route('/api/orders', methods=['GET'])
def get_orders():
    """Obtiene todas las órdenes con filtros opcionales"""
    date_filter = request.args.get('date')
    status = request.args.get('status')
    
    query = Order.query
    
    if date_filter:
        target_date = datetime.strptime(date_filter, '%Y-%m-%d').date()
        query = query.filter(db.func.date(Order.created_at) == target_date)
    
    if status:
        query = query.filter_by(status=status)
    
    orders = query.order_by(Order.created_at.desc()).all()
    return jsonify([order.to_dict() for order in orders])


@app.route('/api/orders/<int:order_id>', methods=['GET'])
def get_order(order_id):
    """Obtiene una orden específica"""
    order = Order.query.get_or_404(order_id)
    return jsonify(order.to_dict())


@app.route('/api/orders/<int:order_id>/cancel', methods=['PUT'])
def cancel_order(order_id):
    """Cancela una orden"""
    order = Order.query.get_or_404(order_id)
    order.status = 'cancelled'
    db.session.commit()
    
    return jsonify(order.to_dict())


# ============= RUTAS DE REPORTES =============

@app.route('/api/reports/daily', methods=['GET'])
def get_daily_report():
    """Obtiene el reporte de ventas del día"""
    target_date = request.args.get('date')
    
    if target_date:
        target_date = datetime.strptime(target_date, '%Y-%m-%d').date()
    else:
        target_date = date.today()
    
    # Buscar ventas del día
    daily_sales = DailySales.query.filter_by(date=target_date).first()
    
    if not daily_sales:
        return jsonify({
            'date': target_date.isoformat(),
            'total_orders': 0,
            'total_sales': 0.0,
            'total_iva': 0.0,
            'cash_sales': 0.0,
            'card_sales': 0.0
        })
    
    return jsonify(daily_sales.to_dict())


@app.route('/api/reports/best-sellers', methods=['GET'])
def get_best_sellers():
    """Obtiene los productos más vendidos"""
    days = request.args.get('days', 7, type=int)
    
    # Subconsulta para obtener ventas por producto
    result = db.session.query(
        MenuItem.name,
        MenuItem.category,
        db.func.sum(OrderItem.quantity).label('total_sold'),
        db.func.sum(OrderItem.subtotal).label('total_revenue')
    ).join(OrderItem.menu_item).join(OrderItem.order).filter(
        Order.created_at >= datetime.now() - timedelta(days=days),
        Order.status == 'completed'
    ).group_by(MenuItem.id).order_by(db.desc('total_sold')).limit(10).all()
    
    return jsonify([{
        'name': r[0],
        'category': r[1],
        'total_sold': r[2],
        'total_revenue': float(r[3])
    } for r in result])


@app.route('/api/reports/sales-by-category', methods=['GET'])
def get_sales_by_category():
    """Obtiene ventas agrupadas por categoría"""
    days = request.args.get('days', 7, type=int)
    
    from datetime import timedelta
    
    result = db.session.query(
        MenuItem.category,
        db.func.count(OrderItem.id).label('items_sold'),
        db.func.sum(OrderItem.subtotal).label('total_revenue')
    ).join(OrderItem.menu_item).join(OrderItem.order).filter(
        Order.created_at >= datetime.now() - timedelta(days=days),
        Order.status == 'completed'
    ).group_by(MenuItem.category).all()
    
    return jsonify([{
        'category': r[0],
        'items_sold': r[1],
        'total_revenue': float(r[2])
    } for r in result])


# ============= FUNCIONES AUXILIARES =============

def update_daily_sales(order):
    """Actualiza el resumen de ventas diarias"""
    today = date.today()
    daily_sales = DailySales.query.filter_by(date=today).first()
    
    if not daily_sales:
        daily_sales = DailySales(
            date=today,
            total_orders=0,
            total_sales=0.0,
            total_iva=0.0,
            cash_sales=0.0,
            card_sales=0.0
        )
        db.session.add(daily_sales)
    
    daily_sales.total_orders += 1
    daily_sales.total_sales += order.total
    daily_sales.total_iva += order.iva
    
    if order.payment_method == 'cash':
        daily_sales.cash_sales += order.total
    elif order.payment_method == 'card':
        daily_sales.card_sales += order.total


# ============= RUTA PRINCIPAL =============

@app.route('/')
def index():
    return jsonify({
        'message': 'API del Sistema POS - La Cantina Mexicana',
        'version': '1.0',
        'endpoints': {
            'menu': '/api/menu',
            'orders': '/api/orders',
            'reports': '/api/reports/daily'
        }
    })


if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=5000)
