# Restaurante POS API – Las Tres Marias

Backend en Flask para gestionar menú, órdenes, reportes y tickets PDF, con sistema de roles (admin, cajero, mesero) y gestión de tickets abiertos.

## 🚀 Características principales

- **Sistema de autenticación JWT** con 3 roles:
  - **Admin (Caja/Gerente)**: Acceso completo, reportes, gestión de menú
  - **Cajero**: Crear/completar órdenes, generar tickets
  - **Mesero**: Crear tickets abiertos, agregar/modificar items

- **Tickets abiertos**: Los meseros pueden crear tickets y seguir agregando items mientras el cliente decide
- **Tipos de orden**: Local, para llevar, a domicilio (con datos de contacto)
- **Generación de tickets PDF** con información completa
- **Reportes de ventas** diarias y análisis

## 📋 Requisitos

- Python 3.10+
- SQLite por defecto (puede apuntar a PostgreSQL/MySQL vía `DATABASE_URL`)

## ⚙️ Configuración de entorno

Crea un archivo `.env` en la raíz:

```env
FLASK_ENV=development
SECRET_KEY=tu-secreto-aqui
JWT_SECRET_KEY=otro-secreto-jwt
DATABASE_URL=sqlite:///restaurant.db
ADMIN_USERNAME=admin
ADMIN_PASSWORD=admin123
```

## 📦 Instalación y ejecución

```bash
# Crear entorno virtual
python -m venv venv

# Activar entorno virtual
# Windows:
venv\Scripts\activate
# Linux/Mac:
source venv/bin/activate

# Instalar dependencias
pip install -r requirements.txt

# Ejecutar servidor
python app.py
```

Servidor: http://localhost:5000  
Swagger: http://localhost:5000/apidocs

## 👥 Usuarios por defecto

Al iniciar por primera vez, se crean estos usuarios:

| Usuario | Contraseña | Rol |
|---------|------------|-----|
| admin | admin123 | admin |
| cajero1 | cajero123 | cashier |
| mesero1 | mesero123 | waiter |

## 🔐 Autenticación

### Login

```http
POST /api/auth/login
Content-Type: application/json

{
  "username": "mesero1",
  "password": "mesero123"
}
```

**Respuesta:**
```json
{
  "access_token": "eyJ0eXAiOiJKV1QiLCJhbGc...",
  "user": {
    "id": 3,
    "username": "mesero1",
    "full_name": "Juan Pérez",
    "role": "waiter"
  }
}
```

Usa el token en las siguientes peticiones:
```http
Authorization: Bearer eyJ0eXAiOiJKV1QiLCJhbGc...
```

## 📝 Flujo de trabajo típico

### 1. Mesero crea ticket abierto

```http
POST /api/orders/
Authorization: Bearer <token-mesero>
Content-Type: application/json

{
  "customer_name": "Mesa 5",
  "order_type": "local",
  "items": [
    {
      "id": 1,
      "quantity": 2,
      "notes": "Sin cebolla"
    }
  ]
}
```

La orden se crea con `status: "open"` y se puede seguir modificando.

### 2. Mesero agrega más items

```http
POST /api/orders/{order_id}/items
Authorization: Bearer <token-mesero>
Content-Type: application/json

{
  "items": [
    {
      "id": 6,
      "quantity": 2
    }
  ]
}
```

### 3. Mesero modifica cantidad de un item

```http
PUT /api/orders/{order_id}/items/{item_id}
Authorization: Bearer <token-mesero>
Content-Type: application/json

{
  "quantity": 3,
  "notes": "Agregar limón"
}
```

### 4. Mesero elimina un item

```http
DELETE /api/orders/{order_id}/items/{item_id}
Authorization: Bearer <token-mesero>
```

### 5. Cajero completa y cobra la orden

```http
PUT /api/orders/{order_id}/complete
Authorization: Bearer <token-cajero>
Content-Type: application/json

{
  "payment_method": "card"
}
```

### 6. Cajero genera el ticket PDF

```http
GET /api/orders/{order_id}/ticket
Authorization: Bearer <token-cajero>
```

Descarga el PDF del ticket.

## 📋 Endpoints principales

### Autenticación (`/api/auth`)

| Método | Ruta | Descripción | Roles |
|--------|------|-------------|-------|
| POST | `/login` | Iniciar sesión | Público |

### Menú (`/api/menu`)

| Método | Ruta | Descripción | Roles |
|--------|------|-------------|-------|
| GET | `/` | Listar menú | Público |
| GET | `/{id}` | Obtener item | Público |
| POST | `/` | Crear item | admin |
| PUT | `/{id}` | Actualizar item | admin |
| DELETE | `/{id}` | Eliminar item | admin |
| GET | `/categories` | Listar categorías | Público |

### Órdenes (`/api/orders`)

| Método | Ruta | Descripción | Roles |
|--------|------|-------------|-------|
| POST | `/` | Crear ticket abierto | admin, cashier, waiter |
| GET | `/` | Listar órdenes | admin, cashier, waiter |
| GET | `/open` | Listar tickets abiertos | admin, cashier, waiter |
| GET | `/{id}` | Obtener orden | admin, cashier, waiter |
| POST | `/{id}/items` | Agregar items | admin, cashier, waiter |
| PUT | `/{id}/items/{item_id}` | Modificar item | admin, cashier, waiter |
| DELETE | `/{id}/items/{item_id}` | Eliminar item | admin, cashier, waiter |
| PUT | `/{id}/complete` | Completar orden | admin, cashier |
| PUT | `/{id}/cancel` | Cancelar orden | admin, cashier |
| GET | `/{id}/ticket` | Descargar PDF | admin, cashier |

### Reportes (`/api/reports`)

| Método | Ruta | Descripción | Roles |
|--------|------|-------------|-------|
| GET | `/daily` | Reporte diario | admin |
| GET | `/best-sellers` | Más vendidos | admin |
| GET | `/sales-by-category` | Ventas por categoría | admin |

## 🍕 Tipos de orden

### Local (en el restaurante)
```json
{
  "order_type": "local",
  "customer_name": "Mesa 5"
}
```

### Para llevar
```json
{
  "order_type": "takeout",
  "customer_name": "Juan Pérez"
}
```

### A domicilio
```json
{
  "order_type": "delivery",
  "customer_name": "María García",
  "delivery_phone": "33-1234-5678",
  "delivery_address": "Calle Morelos 123, Col. Centro"
}
```

**Nota:** Las órdenes a domicilio requieren teléfono y dirección obligatorios.

## 🧪 Tests

```bash
pytest
```

Los tests incluyen:
- Autenticación de todos los roles
- Creación de tickets abiertos
- Agregar/modificar/eliminar items
- Completar órdenes
- Órdenes a domicilio
- Permisos por rol

## 🐳 Docker

### Docker simple

```bash
docker build -t restaurante-api .
docker run -p 5000:5000 --env-file .env restaurante-api
```

### Docker Compose (con PostgreSQL)

```bash
docker-compose up --build
```

## 🗄️ Migraciones

```bash
# Inicializar migraciones
flask --app app:create_app db init

# Crear migración
flask --app app:create_app db migrate -m "descripcion"

# Aplicar migración
flask --app app:create_app db upgrade
```

## 🔒 Permisos por rol

| Acción | Admin | Cajero | Mesero |
|--------|-------|--------|--------|
| Ver menú | ✅ | ✅ | ✅ |
| Editar menú | ✅ | ❌ | ❌ |
| Crear ticket abierto | ✅ | ✅ | ✅ |
| Agregar items a ticket | ✅ | ✅ | ✅ |
| Completar orden | ✅ | ✅ | ❌ |
| Cancelar orden | ✅ | ✅ | ❌ |
| Generar PDF | ✅ | ✅ | ❌ |
| Ver reportes | ✅ | ❌ | ❌ |

## 📁 Estructura del proyecto

```
restaurante_app/
├── api/
│   ├── __init__.py
│   ├── auth_routes.py          # Autenticación
│   ├── menu_routes.py          # Gestión de menú
│   ├── order_routes.py         # Gestión de órdenes (mejorado)
│   └── report_routes.py        # Reportes
├── utils/
│   └── ticket_generator.py     # Generador de PDFs (mejorado)
├── tests/
│   └── test_api.py            # Tests (actualizados)
├── app.py                      # Aplicación principal
├── models.py                   # Modelos DB (mejorados)
├── database.py                 # Inicialización DB (mejorada)
├── auth_utils.py              # Decoradores JWT (mejorados)
├── config.py                   # Configuración
├── errors.py                   # Manejo de errores
├── requirements.txt
├── Dockerfile
├── docker-compose.yml
└── README.md
```

## 🚀 Mejoras implementadas

### ✨ Sistema de roles completo
- Admin (caja/gerente): control total
- Cajero: operaciones de punto de venta
- Mesero: toma de órdenes

### 📝 Tickets abiertos
- Crear ticket sin completarlo
- Agregar items en cualquier momento
- Modificar cantidades y notas
- Eliminar items
- El cajero completa y cobra

### 🚚 Tipos de orden
- Local: órdenes en el restaurante
- Para llevar: órdenes para recoger
- A domicilio: con teléfono y dirección obligatorios

### 🧾 Tickets PDF mejorados
- Muestra tipo de orden
- Datos de contacto para domicilio
- Notas por producto
- Método de pago

## 🤝 Contribuir

1. Crea una rama (`git checkout -b feature/nueva-funcionalidad`)
2. Ejecuta los tests (`pytest`)
3. Si cambias modelos, genera migración
4. Envía PR con descripción clara

## 📄 Licencia

Copyright (c) 2025 Restaurante App  
Desarrollado por: Jose Angel Rodriguez Ramirez