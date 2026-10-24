import os

import click
from flask import Flask
from flask_login import LoginManager, current_user
from flask_migrate import Migrate, upgrade
from flask_sqlalchemy import SQLAlchemy
from flask_wtf.csrf import CSRFProtect

from config import DevelopmentConfig, ProductionConfig

db = SQLAlchemy()
migrate = Migrate()
login_manager = LoginManager()
csrf = CSRFProtect()


def create_app(config_class=None):
    app = Flask(__name__, instance_relative_config=True)
    selected_config = config_class or (
        ProductionConfig
        if os.environ.get("FLASK_ENV") == "production"
        else DevelopmentConfig
    )
    if selected_config is ProductionConfig and not os.environ.get("SECRET_KEY"):
        raise RuntimeError("Define SECRET_KEY antes de iniciar en producción.")
    app.config.from_object(selected_config)
    os.makedirs(app.instance_path, exist_ok=True)

    db.init_app(app)
    migrate.init_app(app, db)
    login_manager.init_app(app)
    csrf.init_app(app)
    login_manager.login_view = "auth.login"
    login_manager.login_message = "Inicia sesión para continuar."
    login_manager.login_message_category = "info"

    from app import models
    from app.auth.routes import auth_bp
    from app.clientes.routes import clientes_bp
    from app.main.routes import main_bp
    from app.pagos.routes import pagos_bp
    from app.reportes.routes import reportes_bp
    from app.reservas.routes import reservas_bp
    from app.unidades.routes import unidades_bp
    from app.choferes.routes import choferes_bp
    from app.api.routes import api_bp

    app.register_blueprint(auth_bp)
    app.register_blueprint(main_bp)
    app.register_blueprint(clientes_bp)
    app.register_blueprint(unidades_bp)
    app.register_blueprint(choferes_bp)
    app.register_blueprint(reservas_bp)
    app.register_blueprint(pagos_bp)
    app.register_blueprint(reportes_bp)
    app.register_blueprint(api_bp)

    @app.cli.command("init-db")
    def init_db_command():
        """Create the database tables and the first administrator."""
        upgrade()
        click.echo("Esquema de base de datos actualizado.")
        if not models.Usuario.query.first():
            email = os.environ.get("ADMIN_EMAIL") or click.prompt("Correo del administrador")
            password = os.environ.get("ADMIN_PASSWORD") or click.prompt(
                "Contraseña del administrador", hide_input=True, confirmation_prompt=True
            )
            if "@" not in email or len(password) < 12:
                raise click.ClickException(
                    "Usa un correo válido y una contraseña de al menos 12 caracteres."
                )
            user = models.Usuario(
                nombre="Administrador",
                email=email.strip().lower(),
                rol="administrador",
            )
            user.set_password(password)
            db.session.add(user)
            db.session.commit()
            click.echo("Administrador inicial creado.")
        else:
            click.echo("Ya existe al menos un usuario; no se creó otro administrador.")

    @app.cli.command("create-user")
    def create_user():
        """Create a role-specific user account."""
        roles = ("administrador", "operaciones", "ventas", "chofer", "cliente")
        nombre = click.prompt("Nombre")
        email = click.prompt("Correo").strip().lower()
        role = click.prompt("Rol", type=click.Choice(roles))
        password = click.prompt("Contraseña", hide_input=True, confirmation_prompt=True)
        if "@" not in email or len(password) < 12:
            raise click.ClickException(
                "Usa un correo válido y una contraseña de al menos 12 caracteres."
            )
        if models.Usuario.query.filter_by(email=email).first():
            raise click.ClickException("Ya existe una cuenta con ese correo.")

        user = models.Usuario(nombre=nombre.strip(), email=email, rol=role)
        if role == "chofer":
            drivers = models.Chofer.query.order_by(models.Chofer.apellidos).all()
            if not drivers:
                raise click.ClickException("Registra un chofer antes de crear su cuenta.")
            click.echo("Choferes:")
            for driver in drivers:
                click.echo(f"{driver.id}: {driver.nombre} {driver.apellidos}")
            driver_id = click.prompt("ID del chofer", type=int)
            if not db.session.get(models.Chofer, driver_id):
                raise click.ClickException("El ID de chofer no existe.")
            user.chofer_id = driver_id
        elif role == "cliente":
            clients = models.Cliente.query.order_by(models.Cliente.nombre).all()
            if not clients:
                raise click.ClickException("Registra un cliente antes de crear su cuenta.")
            click.echo("Clientes:")
            for client in clients:
                click.echo(f"{client.id}: {client.nombre}")
            client_id = click.prompt("ID del cliente", type=int)
            if not db.session.get(models.Cliente, client_id):
                raise click.ClickException("El ID de cliente no existe.")
            user.cliente_id = client_id
        user.set_password(password)
        db.session.add(user)
        db.session.commit()
        click.echo("Usuario creado.")

    @app.cli.command("seed-demo")
    def seed_demo():
        """Add sample customers, vehicles and drivers for a local demo."""
        from db.seed import seed_demo_data

        seed_demo_data()
        click.echo("Datos de demostración listos.")

    @app.context_processor
    def inject_navigation():
        return {"navigation_user": current_user}

    return app
