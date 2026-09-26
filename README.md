# Fullstack authentication foundation

Base fullstack para proyectos web orientados a portfolio, construida para practicar y demostrar un flujo completo entre frontend, API, autenticación y base de datos.

Este repositorio es el punto de partida del proyecto. Antes de definir la aplicación de inventario de alimentos, el objetivo era construir una base reutilizable para futuras aplicaciones web basadas en API, con el frontend y el backend ejecutándose en Docker.

## Estado actual

Está implementada una primera versión funcional de autenticación local:

- Registro con email y contraseña.
- Validación de contraseña de 8 caracteres o más, con letra, número y carácter especial.
- Verificación de email mediante enlace enviado por SMTP.
- Inicio de sesión con cookies `HttpOnly` para los tokens de autenticación.
- Access token JWT de corta duración.
- Refresh tokens persistidos y revocables.
- Protección CSRF para operaciones mutables.
- Cierre de sesión.
- Renovación de sesión.
- Recuperación y restablecimiento de contraseña por email.
- Cambio de contraseña.
- Cambio de email con nueva verificación.
- Consulta y revocación de sesiones activas.
- Eliminación de cuenta.
- Rate limiting básico en memoria para algunas operaciones sensibles.
- Limpieza de tokens vencidos en operaciones de autenticación.
- Migraciones de base de datos con Alembic.
- Frontend React funcional para los flujos principales.
- API documentada automáticamente mediante Swagger UI.
- Servicios de frontend, backend y PostgreSQL dockerizados.

La autenticación local es funcional para desarrollo y aprendizaje, pero todavía requiere trabajo antes de considerarse apta para producción. Las limitaciones conocidas están resumidas más abajo y detalladas en `faltantes.md`, que se mantiene ignorado para seguimiento personal.

## Objetivo original

El objetivo inicial era aprender y demostrar un stack fullstack completo creando una base que después pudiera reutilizarse en distintas aplicaciones:

```text
Frontend React
       |
       v
API FastAPI
       |
       v
PostgreSQL
```

La base debía resolver primero los problemas transversales —usuarios, sesiones, contraseñas, email y persistencia— para luego permitir construir funcionalidades de negocio sobre una API autenticada.

El proyecto de inventario de alimentos, lista del supermercado y recomendaciones de recetas con IA será la siguiente aplicación que se construirá a partir de este baseline. El roadmap correspondiente está en `roadmap.md`.

## Stack tecnológico

### Backend

- Python 3.12.
- FastAPI.
- SQLAlchemy 2.
- Pydantic Settings.
- Alembic.
- PostgreSQL 16.
- Psycopg 3.
- PyJWT.
- Argon2 mediante `pwdlib` para hash de contraseñas.
- SMTP para envío de emails.

### Frontend

- React 19.
- Vite 7.
- JavaScript.
- HTML y CSS.

### Infraestructura local

- Docker Compose.
- PostgreSQL en contenedor.
- FastAPI en contenedor.
- React compilado y servido por Nginx en contenedor.

## Estructura principal

```text
.
├── backend/
│   ├── app/
│   │   ├── api/             # Dependencias y rutas HTTP
│   │   ├── core/            # Configuración
│   │   ├── models/          # Modelos SQLAlchemy
│   │   ├── schemas/         # Esquemas Pydantic
│   │   ├── db.py            # Sesiones de base de datos
│   │   ├── security.py      # Hash y tokens
│   │   └── main.py          # Aplicación FastAPI
│   ├── migrations/          # Migraciones Alembic
│   ├── tests/               # Pruebas actuales
│   ├── Dockerfile
│   └── requirements.txt
├── frontend/
│   ├── src/
│   │   ├── main.jsx
│   │   ├── config.js
│   │   └── styles.css
│   ├── Dockerfile
│   └── package.json
├── docker-compose.yml
├── .env.example
├── README-Docker.md
├── faltantes.md             # Ignorado; seguimiento personal
└── roadmap.md
```

## Ejecutar localmente con Docker

### Requisitos

- Docker Desktop instalado y ejecutándose.
- Git.
- Una cuenta SMTP para probar el envío de emails. Durante el desarrollo actual se utiliza una cuenta personal de Gmail mediante contraseña de aplicación.

### Configuración

1. Copiar `.env.example` como `.env` en la raíz del proyecto.
2. Completar `backend/.env` con la configuración requerida por la API.
3. No subir archivos `.env` ni credenciales al repositorio.

La variable `API_URL` debe contener solamente el origen de la API:

```env
API_URL=http://localhost:8000
FRONTEND_URL=http://localhost:5173
```

El frontend agrega `/api` desde el código. En producción, la idea es cambiar únicamente el origen:

```env
API_URL=https://api.midominio.com
```

### Arranque

Desde la raíz:

```powershell
docker compose up --build
```

La API ejecuta las migraciones pendientes antes de iniciar Uvicorn.

### URLs locales

- Frontend: [http://localhost:5173](http://localhost:5173)
- Documentación Swagger: [http://localhost:8000/docs](http://localhost:8000/docs)
- Health check: [http://localhost:8000/health](http://localhost:8000/health)

## Flujos disponibles

### Registro y verificación

1. El usuario completa email y contraseña.
2. La API guarda la contraseña hasheada, nunca en texto plano.
3. Se genera un token de verificación de un solo uso y con vencimiento.
4. Se envía un enlace por email.
5. El usuario confirma su email antes de iniciar sesión.

### Login y sesiones

Después de autenticarse, la API establece cookies para la sesión. El access token es de duración corta y el refresh token se persiste para poder revocarlo.

Las sesiones guardan metadatos básicos —user agent, IP y fecha de último uso— para poder listarlas y revocarlas desde la cuenta.

### Recuperación de contraseña

El usuario solicita un enlace con su email y define una contraseña nueva mediante un token temporal. Al cambiar la contraseña se revocan las sesiones existentes.

### Cuenta

El usuario autenticado puede:

- Cambiar su contraseña.
- Cambiar su email y volver a verificarlo.
- Ver sus sesiones activas.
- Revocar una sesión.
- Cerrar sesión.
- Eliminar la cuenta.

## API de autenticación

La API se expone bajo `/api`.

| Método | Ruta | Propósito |
| --- | --- | --- |
| `POST` | `/api/auth/register` | Crear una cuenta |
| `GET` | `/api/auth/verify-email` | Verificar el email |
| `POST` | `/api/auth/resend-verification` | Reenviar verificación |
| `POST` | `/api/auth/login` | Iniciar sesión |
| `POST` | `/api/auth/refresh` | Renovar la sesión |
| `POST` | `/api/auth/logout` | Cerrar sesión |
| `POST` | `/api/auth/forgot-password` | Solicitar recuperación |
| `POST` | `/api/auth/reset-password` | Restablecer contraseña |
| `GET` | `/api/auth/me` | Consultar usuario actual |
| `POST` | `/api/auth/change-password` | Cambiar contraseña |
| `POST` | `/api/auth/change-email` | Cambiar email |
| `GET` | `/api/auth/sessions` | Listar sesiones activas |
| `DELETE` | `/api/auth/sessions/{session_id}` | Revocar una sesión |
| `DELETE` | `/api/auth/account` | Eliminar cuenta |

Para probar los endpoints de manera interactiva se puede usar Swagger UI en `/docs`.

## Base de datos y migraciones

La aplicación usa PostgreSQL dentro de Docker Compose y ejecuta Alembic al iniciar la API.

Migraciones actuales:

1. `0001_create_users`: crea usuarios.
2. `0002_email_verification`: agrega verificación de email.
3. `0003_auth_hardening`: agrega refresh tokens y tokens de recuperación.
4. `0004_session_metadata`: agrega información de las sesiones.

Para consultar usuarios desde el contenedor:

```powershell
docker compose exec postgres psql -U portfolio -d portfolio -c "SELECT id, email, is_email_verified, created_at FROM users;"
```

Para entrar a PostgreSQL de forma interactiva:

```powershell
docker compose exec postgres psql -U portfolio -d portfolio
```

Salir de `psql`:

```sql
\q
```

El volumen `postgres_data` permite conservar los datos entre reinicios normales de los contenedores. Ese volumen no reemplaza un backup.

## Variables de entorno

El archivo `.env.example` contiene la configuración pública mínima para Docker Compose. La configuración sensible de la API se mantiene en `backend/.env` y no debe commitearse.

Entre las variables relevantes se encuentran:

- URL de base de datos.
- Secreto y algoritmo JWT.
- Duración de access y refresh tokens.
- Origen permitido del frontend.
- Configuración de cookies.
- Host, puerto y credenciales SMTP.
- Duración de los tokens de verificación y recuperación.

En producción, los secretos deberían trasladarse a un gestor de secretos y las cookies deberían ejecutarse con `Secure` detrás de HTTPS.

## Pruebas y calidad actual

Existe una primera prueba de autenticación en `backend/tests/test_auth.py` y las dependencias de testing están incluidas en `backend/requirements.txt`.

La cobertura todavía no es suficiente para afirmar que el sistema está listo para producción. Antes de publicar una beta se deben ampliar las pruebas para registro, verificación, login, refresh, logout, revocación, recuperación, cambio de email, eliminación de cuenta, aislamiento entre usuarios y comportamiento ante errores de correo.

## Pendientes antes de producción

Los principales pendientes son:

- Dominio real, HTTPS y configuración segura de cookies.
- PostgreSQL administrado, backups automáticos y prueba de restauración.
- Rate limiting compartido y resistente a múltiples réplicas.
- Detección de reutilización de refresh tokens.
- Pruebas automatizadas más completas.
- Proveedor de email transaccional en lugar de una cuenta personal de Gmail.
- SPF, DKIM y DMARC para el dominio de envío.
- Logs estructurados, monitoreo, alertas y limpieza programada de tokens.
- Revisión de cookies, CSRF y CORS con la topología de producción.
- Login con Google, incluyendo OAuth, validación de identidad y vinculación segura de cuentas.

La lista detallada de seguimiento personal está en `faltantes.md`. Ese archivo está incluido en `.gitignore` intencionalmente.

## Próxima aplicación

Este repositorio será clonado como base para construir una app de inventario de alimentos y lista del supermercado.

El alcance planificado incluye:

- Inventario por ubicación: heladera, alacena y vista de especias/condimentos.
- Lista de compras con ítems alimenticios y no alimenticios, como productos de limpieza.
- Confirmación para agregar un alimento agotado a la lista.
- Recomendaciones de recetas basadas en el stock.
- Posibles funciones futuras de suscripción, como escaneo de códigos o lectura de tickets.

El plan de trabajo está documentado en `roadmap.md`.

## Licencia

Proyecto personal de aprendizaje y portfolio. No se definió todavía una licencia para distribución pública.
