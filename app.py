import logging
import os

from dotenv import load_dotenv
from flask import Flask, jsonify
from flask_cors import CORS
from flask_jwt_extended import JWTManager
from flask_migrate import Migrate
from flasgger import Swagger

from config import DevelopmentConfig, config_by_name
from database import db, init_db
from errors import register_error_handlers

migrate = Migrate()
jwt = JWTManager()
swagger = Swagger()


def create_app(config_name: str | None = None) -> Flask:
    """Crea y configura la aplicación Flask."""
    load_dotenv()
    app = Flask(__name__)

    env_name = config_name or os.getenv("FLASK_ENV") or os.getenv("ENV") or "development"
    app.config.from_object(config_by_name.get(env_name, DevelopmentConfig))

    # CORS para desarrollo (en producción, especifica orígenes permitidos)
    CORS(app)

    # Inicializar extensiones
    db.init_app(app)
    migrate.init_app(app, db)
    jwt.init_app(app)

    @jwt.unauthorized_loader
    def _unauthorized_callback(msg):
        return jsonify({"error": "Unauthorized", "message": msg}), 401

    @jwt.invalid_token_loader
    def _invalid_token_callback(msg):
        return jsonify({"error": "Invalid token", "message": msg}), 422

    @jwt.expired_token_loader
    def _expired_token_callback(jwt_header, jwt_payload):
        return jsonify({"error": "Token expired"}), 401

    # Registrar blueprints
    from api.menu_routes import menu_bp
    from api.order_routes import order_bp
    from api.report_routes import report_bp
    from api.auth_routes import auth_bp

    app.register_blueprint(menu_bp, url_prefix="/api/menu")
    app.register_blueprint(order_bp, url_prefix="/api/orders")
    app.register_blueprint(report_bp, url_prefix="/api/reports")
    app.register_blueprint(auth_bp, url_prefix="/api/auth")

    # Manejadores de error globales
    register_error_handlers(app)

    # Crear tablas y seeds iniciales
    init_db(app)

    swagger.init_app(
        app,
        template={
            "swagger": "2.0",
            "info": {
                "title": "API POS - La Cantina Mexicana",
                "description": "Documentación de la API",
                "version": "1.0.0",
            },
        },
    )

    @app.route("/")
    def index():
        return jsonify(
            {
                "message": "API del Sistema POS - La Cantina Mexicana",
                "version": "1.0",
                "endpoints": {
                    "menu": "/api/menu",
                    "orders": "/api/orders",
                    "reports": {
                        "daily": "/api/reports/daily",
                        "best_sellers": "/api/reports/best-sellers",
                        "sales_by_category": "/api/reports/sales-by-category",
                    },
                    "auth": "/api/auth/login",
                },
            }
        )

    configure_logging(app)
    return app


def configure_logging(app: Flask) -> None:
    """Configura logging básico."""
    log_level = logging.DEBUG if app.config.get("DEBUG") else logging.INFO
    logging.basicConfig(
        level=log_level,
        format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    )


if __name__ == "__main__":
    application = create_app()
    application.run(host="0.0.0.0", port=5000, debug=application.config.get("DEBUG", False))
