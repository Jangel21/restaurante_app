from functools import wraps
from flask import jsonify
from flask_jwt_extended import verify_jwt_in_request, get_jwt


def role_required(*roles):
    """
    Decorador para validar roles usando JWT.
    Ejemplo: @role_required("admin") o @role_required("admin", "cashier", "waiter")
    """

    def wrapper(fn):
        @wraps(fn)
        def decorator(*args, **kwargs):
            verify_jwt_in_request()
            claims = get_jwt()
            user_role = claims.get("role")
            if user_role not in roles:
                return jsonify({"error": "Forbidden", "message": "No tienes permisos para esta acción"}), 403
            return fn(*args, **kwargs)

        return decorator

    return wrapper


def get_current_user_id():
    """Obtiene el ID del usuario actual del JWT."""
    verify_jwt_in_request()
    claims = get_jwt()
    return claims.get("sub")  # 'sub' es el identity (user.id)


def get_current_user_role():
    """Obtiene el rol del usuario actual del JWT."""
    verify_jwt_in_request()
    claims = get_jwt()
    return claims.get("role")