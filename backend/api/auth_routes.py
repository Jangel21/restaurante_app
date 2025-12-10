from flask import Blueprint, jsonify, request
from flask_jwt_extended import create_access_token

from models import User

auth_bp = Blueprint("auth_bp", __name__)


@auth_bp.route("/login", methods=["POST"])
def login():
    """
    Autenticación básica con JWT.
    ---
    tags:
      - auth
    consumes:
      - application/json
    parameters:
      - in: body
        name: body
        schema:
          type: object
          required: [username, password]
          properties:
            username:
              type: string
              example: admin
            password:
              type: string
              example: admin123
    responses:
      200:
        description: Token generado
        schema:
          type: object
          properties:
            access_token:
              type: string
            user:
              type: object
              properties:
                id:
                  type: integer
                username:
                  type: string
                role:
                  type: string
      401:
        description: Credenciales inválidas
    """
    data = request.get_json() or {}
    username = data.get("username")
    password = data.get("password")

    if not username or not password:
        return jsonify({"error": "username y password son obligatorios"}), 400

    user = User.query.filter_by(username=username).first()
    if not user or not user.check_password(password):
        return jsonify({"error": "Credenciales inválidas"}), 401

    access_token = create_access_token(
        identity=user.id, additional_claims={"role": user.role, "username": user.username}
    )

    return jsonify({"access_token": access_token, "user": user.to_dict()})
