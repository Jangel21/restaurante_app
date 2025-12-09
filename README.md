# Restaurante POS API – Las Tres Marias
Backend en Flask para gestionar menú, órdenes, reportes y tickets PDF, ahora con JWT, roles y blueprints.

## Arquitectura rápida
- Frontend → API Flask (`/api/...`) → SQLAlchemy (DB) → TicketGenerator (PDF)
- Blueprints: `menu`, `orders`, `reports`, `auth`
- Config por entorno via `config.py` + variables `.env`
- JWT + roles (`admin`, `cashier`) para proteger endpoints
- Swagger UI disponible en `/apidocs`

## Requisitos
- Python 3.10+
- SQLite por defecto (puede apuntar a PostgreSQL/MySQL vía `DATABASE_URL`)

## Configuración de entorno
Usa `.env` en la raíz (ejemplo):
```
FLASK_ENV=development            # o production/testing
SECRET_KEY=super-secreto
JWT_SECRET_KEY=otro-secreto
DATABASE_URL=sqlite:///restaurant.db
ADMIN_USERNAME=admin
ADMIN_PASSWORD=admin123
```

## Instalación y ejecución
```bash
python -m venv venv
venv\Scripts\activate   # Windows
# source venv/bin/activate   # Linux/Mac
pip install -r requirements.txt
python app.py            # o: flask --app app:create_app run
```
Servidor: http://localhost:5000  
Swagger: http://localhost:5000/apidocs

## Blueprints y endpoints principales
- Menú (`/api/menu`): GET libre; POST/PUT/DELETE requieren rol `admin`.
- Órdenes (`/api/orders`): crear/listar/cancelar; protegidos (`admin`/`cashier`).
  - Descargar ticket: `GET /api/orders/<id>/ticket` → PDF.
- Reportes (`/api/reports`): `daily`, `best-sellers`, `sales-by-category` (rol `admin`).
- Auth (`/api/auth/login`): devuelve `access_token` JWT.

### Formatos de ejemplo
Login:
```http
POST /api/auth/login
{ "username": "admin", "password": "admin123" }
```
Crear orden:
```http
POST /api/orders/
Authorization: Bearer <token>
{
  "customer_name": "Cliente",
  "payment_method": "cash",
  "items": [{ "id": 1, "quantity": 2 }]
}
```

## Configuración por entorno
- `config.py` define `DevelopmentConfig`, `ProductionConfig`, `TestingConfig`.
- Usa `FLASK_ENV`/`ENV` para elegir config. Siempre apunta a `SQLALCHEMY_DATABASE_URI` desde variable para cambiar de DB sin tocar código.

### Ejemplos de URIs
- SQLite: `sqlite:///restaurant.db`
- PostgreSQL: `postgresql+psycopg2://user:pass@host/dbname`
- MySQL: `mysql+pymysql://user:pass@host/dbname`

## Migraciones (Flask-Migrate/Alembic)
```bash
flask --app app:create_app db init
flask --app app:create_app db migrate -m "initial"
flask --app app:create_app db upgrade
```

## Tests
```bash
pytest
```
Incluye pruebas básicas de menú, órdenes y reporte diario.

## Docker rápido
```bash
docker build -t restaurante-api .
docker run -p 5000:5000 --env-file .env restaurante-api
# o con docker-compose (usa Postgres):
docker compose up --build
```

## Contribuir
1. Crea rama (`feat/...`).
2. Ejecuta tests (`pytest`).
3. Si cambias modelos, genera migración (`flask db migrate` + `flask db upgrade`).
4. Envía PR con descripción y notas de seguridad.
