# Sistema de renta de camionetas Sprinter

Aplicación web en Flask para administrar clientes, unidades, choferes, reservas, pagos y reportes. Incluye inicio de sesión por roles, protección CSRF y una API JSON de consulta.

## Requisitos

- Python 3.9 o posterior.
- Para el modo predeterminado no necesitas instalar un servidor de base de datos: usa SQLite y guarda la base en `instance/renta_sprinter.db`.
- MySQL es opcional. Si lo usas, instala MySQL Server y crea un usuario con acceso a la base.
- Si `DATABASE_URL` está vacía en `.env`, la aplicación usa SQLite automáticamente.
- Las variables de entorno definidas en Windows tienen prioridad sobre `.env`; si una `DATABASE_URL` antigua está configurada en PowerShell, límpiala para volver a SQLite con `Remove-Item Env:DATABASE_URL -ErrorAction SilentlyContinue`.

## Instalación y ejecución en Windows PowerShell

Desde la carpeta del proyecto:

```powershell
py -3 -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install --upgrade pip
python -m pip install -r requirements.txt
Copy-Item .env.example .env
notepad .env
flask --app "app:create_app" init-db
flask --app "app:create_app" seed-demo
flask --app "app:create_app" run --debug
```

Antes de correr esos comandos, cambia `SECRET_KEY` en `.env` por una clave aleatoria y privada; puedes generar una con `python -c "import secrets; print(secrets.token_hex(32))"`. `DATABASE_URL` puede quedarse vacía para usar SQLite. Al ejecutar `init-db`, se crean las tablas y se solicita el correo y la contraseña para el primer administrador. Abre <http://127.0.0.1:5000/auth/login> y entra con esas credenciales. `seed-demo` agrega clientes, unidades y choferes de ejemplo; no crea cuentas ni contraseñas predeterminadas.

Si quieres evitar las preguntas interactivas durante `init-db`, define `ADMIN_EMAIL` y `ADMIN_PASSWORD` en PowerShell antes de ejecutarlo. La contraseña debe tener al menos 12 caracteres.

Si PowerShell bloquea la activación del entorno virtual, abre una terminal nueva o ejecuta una vez:

```powershell
Set-ExecutionPolicy -Scope CurrentUser RemoteSigned
```

Para iniciar el proyecto después de configurarlo, activa `.venv` y ejecuta:

```powershell
Remove-Item Env:DATABASE_URL -ErrorAction SilentlyContinue
flask --app "app:create_app" run --debug
```

## Usar MySQL

En `.env`, configura `DATABASE_URL` con los datos de tu instalación; no guardes contraseñas reales en el repositorio:

```dotenv
DATABASE_URL=mysql+pymysql://usuario:contraseña@127.0.0.1:3306/renta_sprinter?charset=utf8mb4
```

La base `renta_sprinter` debe existir antes de ejecutar `init-db`. Si eliges MySQL, crea primero una base vacía:

```sql
CREATE DATABASE renta_sprinter CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;
```

Después `init-db` aplica las migraciones y crea el primer administrador. No ejecutes `db/schema.sql` antes de ese comando: ese archivo crea las tablas directamente. Si prefieres inicializar desde SQL, ejecuta `db/schema.sql`, registra el esquema con `flask --app "app:create_app" db stamp head` y crea el administrador con `flask --app "app:create_app" create-user`.

El esquema inicial anterior del proyecto (tablas `sprinters` y `rentas`) no es compatible con el modelo nuevo. No ejecutes un borrado automático sobre datos existentes: respalda la base primero y usa una base vacía o una migración revisada para conservarlos.

Los cambios futuros al modelo se gestionan con Flask-Migrate. Genera una migración, revísala y aplícala con:

```powershell
flask --app "app:create_app" db migrate -m "describe el cambio"
flask --app "app:create_app" db upgrade
```

En producción, configura `FLASK_ENV=production`, una `SECRET_KEY` aleatoria y una base MySQL; sirve la aplicación por HTTPS para que las cookies seguras funcionen.

La configuración lee también las variables SMTP `MAIL_SERVER`, `MAIL_PORT`, `MAIL_USE_TLS`, `MAIL_USE_SSL`, `MAIL_USERNAME`, `MAIL_PASSWORD` y `MAIL_DEFAULT_SENDER`, usando los mismos nombres del documento. Sin embargo, el sistema aún no envía correos: no se implementaron notificaciones ni la integración SMTP. Para Gmail, utiliza una contraseña de aplicación, no la contraseña habitual de tu cuenta.

## Funcionalidades

- Acceso y cierre de sesión; los usuarios se guardan con hash de contraseña.
- Roles: `administrador`, `operaciones`, `ventas`, `chofer` y `cliente`.
- Administración de clientes, unidades y choferes.
- Cotizaciones y reservas, con validación de disponibilidad de la unidad y del chofer.
- Registro de pagos, control del saldo y estados del pago.
- Reporte de ingresos cobrados por mes y descarga en Excel (`.xlsx`).
- API autenticada: `/api/reservas` y `/api/unidades/disponibles`.

Los usuarios adicionales se crean desde la terminal con `flask --app "app:create_app" create-user`; el comando solicita el rol, una contraseña y, para clientes o choferes, la ficha a vincular. Los permisos de interfaz y rutas se comprueban en el servidor.

## Pruebas

```powershell
python -m unittest discover -s tests -v
```
