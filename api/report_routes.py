from datetime import date, datetime, timedelta

from flask import Blueprint, jsonify, request
from sqlalchemy import func

from auth_utils import role_required
from database import db
from models import DailySales, MenuItem, Order, OrderItem

report_bp = Blueprint("report_bp", __name__)


@report_bp.route("/daily", methods=["GET"])
@role_required("admin")
def get_daily_report():
    """Obtiene el reporte de ventas del día."""
    target_date_str = request.args.get("date")
    if target_date_str:
        target_date = datetime.strptime(target_date_str, "%Y-%m-%d").date()
    else:
        target_date = date.today()

    daily_sales = DailySales.query.filter_by(date=target_date).first()

    if not daily_sales:
        return jsonify(
            {
                "date": target_date.isoformat(),
                "total_orders": 0,
                "total_sales": 0.0,
                "total_iva": 0.0,
                "cash_sales": 0.0,
                "card_sales": 0.0,
            }
        )

    return jsonify(daily_sales.to_dict())


@report_bp.route("/best-sellers", methods=["GET"])
@role_required("admin")
def get_best_sellers():
    """Obtiene los productos más vendidos en los últimos N días (default 7)."""
    days = request.args.get("days", 7, type=int)
    start_date = datetime.now() - timedelta(days=days)

    result = (
        db.session.query(
            MenuItem.name,
            MenuItem.category,
            func.sum(OrderItem.quantity).label("total_sold"),
            func.sum(OrderItem.subtotal).label("total_revenue"),
        )
        .join(OrderItem, OrderItem.menu_item_id == MenuItem.id)
        .join(Order, OrderItem.order_id == Order.id)
        .filter(Order.created_at >= start_date, Order.status == "completed")
        .group_by(MenuItem.id)
        .order_by(func.sum(OrderItem.quantity).desc())
        .limit(10)
        .all()
    )

    return jsonify(
        [
            {
                "name": r[0],
                "category": r[1],
                "total_sold": int(r[2]),
                "total_revenue": float(r[3]),
            }
            for r in result
        ]
    )


@report_bp.route("/sales-by-category", methods=["GET"])
@role_required("admin")
def get_sales_by_category():
    """Obtiene ventas agrupadas por categoría en los últimos N días (default 7)."""
    days = request.args.get("days", 7, type=int)
    start_date = datetime.now() - timedelta(days=days)

    result = (
        db.session.query(
            MenuItem.category,
            func.count(OrderItem.id).label("items_sold"),
            func.sum(OrderItem.subtotal).label("total_revenue"),
        )
        .join(OrderItem, OrderItem.menu_item_id == MenuItem.id)
        .join(Order, OrderItem.order_id == Order.id)
        .filter(Order.created_at >= start_date, Order.status == "completed")
        .group_by(MenuItem.category)
        .all()
    )

    return jsonify(
        [
            {
                "category": r[0],
                "items_sold": int(r[1]),
                "total_revenue": float(r[2]),
            }
            for r in result
        ]
    )
