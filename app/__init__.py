import os
from flask import Flask, render_template
from flask_sqlalchemy import SQLAlchemy
from config import DevelopmentConfig

# Inicializa SQLAlchemy aquí. 
db = SQLAlchemy()

def create_app():
    app = Flask(__name__) 
    app.config.from_object(DevelopmentConfig)
    
    # Vincula la aplicación 'app' a la instancia 'db'
    db.init_app(app)

    # Ahora, ya puedes importar tus modelos y blueprints
    # Importa los modelos de las tres tablas
    from .models import Sprinter, Cliente, Renta
    from app.clientes.routes import clientes_bp
    from app.sprinters.routes import sprinters_bp
    from app.rentas.routes import rentas_bp

    app.register_blueprint(clientes_bp)
    app.register_blueprint(sprinters_bp)
    app.register_blueprint(rentas_bp)

    @app.route("/")
    def index():
        try:
            # Consulta los datos de las tres tablas
            sprinters = Sprinter.query.all()
            clientes = Cliente.query.all()
            rentas = Renta.query.all()
            
            
            return render_template(
                "index.html", 
                sprinters=sprinters, 
                clientes=clientes, 
                rentas=rentas
            )
        except Exception as e:
            # Manejar el error si la conexión a la base de datos falla
            return f"Error al conectar con la base de datos: {e}"

    return app