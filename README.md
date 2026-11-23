# ms-tickets (EntradasYa)

Microservicio de Emisión de Entradas, Renderizado de Boletos en PDF con Código QR y Validación de Acceso para EntradasYa.

* **Tecnología:** Python 3.11+ / FastAPI / SQLAlchemy 2.0 (asíncrono con `asyncpg` y `aiosqlite`) / ReportLab / `qrcode` (Pillow)
* **Puerto:** `8005`
* **Base de datos:** `tickets_db` (PostgreSQL 16)
* **Almacenamiento Local:** `STORAGE_PATH` (por defecto `storage/tickets`)

---

## 1. Características Principales

1. **Emisión en Lote (`POST /api/v1/tickets/batch`):** Invocado por `ms-orders` tras confirmación de pago. Genera registros en base de datos y archivos físicos PDF con códigos QR listos para descarga.
2. **Generación de Código Único:** Formato `EY-<EVENT_SHORT>-<HASH_ALEATORIO>` (ej. `EY-ROCK-8X4N2Q`).
3. **Generación Profesional de Boletos PDF (ReportLab + QR):** Maquetación de boleto digital con encabezado institucional, detalles del evento, titular, sector, precio, código QR incrustado y leyenda legal.
4. **Descarga de Boletos (`GET /api/v1/tickets/{id}/download`):** Servicio directo de archivos binarios `application/pdf` con cabecera `Content-Disposition`.
5. **Validación para Portería (`POST /api/v1/tickets/validate`):** Invocado por `ms-checkin` para validar autenticidad de código y correspondencia con el evento (`200 OK`, `404 INVALID_CODE`, `400 EVENT_MISMATCH`).
6. **Consulta de Tickets por Orden (`GET /api/v1/tickets/order/{orderId}`):** Recupera los boletos emitidos para una orden.
7. **Probes de Salud Estándar 12-Factor:** `GET /health/live` (Liveness) y `GET /health/ready` (Readiness con verificación `SELECT 1` a base de datos).

---

## 2. Variables de Entorno

Configurar mediante `.env` (ver `.env.example`):

```env
PORT=8005
ENVIRONMENT=development
DATABASE_URL=postgresql+asyncpg://tickets_user:tickets_pass@localhost:5432/tickets_db
STORAGE_PATH=storage/tickets
JWT_SECRET=super-secure-shared-secret-entradasya-2026
JWT_ALGORITHM=HS256
INTERNAL_TOKEN=internal-service-secret-entradasya-2026
LOG_LEVEL=INFO
```

---

## 3. Instalación y Ejecución Local

```bash
# Crear entorno virtual con Python 3.11+
python -m venv .venv

# Activar entorno virtual
# En Windows (PowerShell):
.\.venv\Scripts\Activate.ps1
# En Linux / macOS:
source .venv/bin/activate

# Instalar dependencias
pip install -r requirements.txt

# Ejecutar el servicio
python main.py
```

La documentación Swagger interactiva se encuentra disponible en `http://localhost:8005/docs`.

---

## 4. Ejecución de Pruebas Automatizadas

La suite de pruebas utiliza `pytest`, `pytest-asyncio` y base de datos SQLite en memoria con `aiosqlite` para aislamiento total:

```bash
pytest -v
```

## Estado de Verificacion CI/CD

- Pipeline `.github/workflows/ci-develop.yml` verificado con disparo automatico en rama `develop`, generando artifacts descargables e imagenes en GHCR y Docker Hub.
