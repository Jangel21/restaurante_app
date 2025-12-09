from flask import Blueprint, jsonify, request

from auth_utils import role_required
from database import db
from models import MenuItem

menu_bp = Blueprint("menu_bp", __name__)


# ==========================
# RUTAS DEL MENÚ
# ==========================

@menu_bp.route("/", methods=["GET"])
def get_menu():
    """
    Obtiene todos los items del menú.
    Opcional: ?category=<nombre> (ignora 'Todos')
    """
    category = request.args.get("category")
    query = MenuItem.query.filter_by(available=True)

    if category and category != "Todos":
        query = query.filter_by(category=category)

    items = query.all()
    return jsonify([item.to_dict() for item in items])


@menu_bp.route("/<int:item_id>", methods=["GET"])
def get_menu_item(item_id):
    """Obtiene un item específico del menú."""
    item = MenuItem.query.get_or_404(item_id)
    return jsonify(item.to_dict())


@menu_bp.route("/", methods=["POST"])
@role_required("admin")
def create_menu_item():
    """Crea un nuevo item en el menú."""
    data = request.get_json() or {}

    required_fields = ["name", "price", "category"]
    if not all(field in data for field in required_fields):
        return jsonify({"error": "Faltan campos obligatorios"}), 400

    new_item = MenuItem(
        name=data["name"],
        price=data["price"],
        category=data["category"],
        description=data.get("description"),
        available=data.get("available", True),
        image_url=data.get("image_url"),
    )

    db.session.add(new_item)
    db.session.commit()
    return jsonify(new_item.to_dict()), 201


@menu_bp.route("/<int:item_id>", methods=["PUT"])
@role_required("admin")
def update_menu_item(item_id):
    """Actualiza un item del menú."""
    item = MenuItem.query.get_or_404(item_id)
    data = request.get_json() or {}

    item.name = data.get("name", item.name)
    item.price = data.get("price", item.price)
    item.category = data.get("category", item.category)
    item.description = data.get("description", item.description)
    item.available = data.get("available", item.available)
    item.image_url = data.get("image_url", item.image_url)

    db.session.commit()
    return jsonify(item.to_dict())


@menu_bp.route("/<int:item_id>", methods=["DELETE"])
@role_required("admin")
def delete_menu_item(item_id):
    """Elimina un item del menú."""
    item = MenuItem.query.get_or_404(item_id)
    db.session.delete(item)
    db.session.commit()
    return jsonify({"message": "Item eliminado correctamente"}), 200


@menu_bp.route("/categories", methods=["GET"])
def get_categories():
    """Obtiene todas las categorías disponibles."""
    categories = db.session.query(MenuItem.category).distinct().all()
    return jsonify([cat[0] for cat in categories])
