from . import db

class Cliente(db.Model):
    __tablename__ = 'clientes'
    id_cliente = db.Column(db.Integer, primary_key=True)
    nombre = db.Column(db.String(100), nullable=False)
    telefono = db.Column(db.String(20))
    correo = db.Column(db.String(100))
    rentas = db.relationship('Renta', backref='cliente', lazy=True)

class Sprinter(db.Model):
    __tablename__ = 'sprinters'
    id_sprinter = db.Column(db.Integer, primary_key=True)
    modelo = db.Column(db.String(50), nullable=False)
    placas = db.Column(db.String(20), nullable=False)
    disponible = db.Column(db.Boolean, default=True)
    rentas = db.relationship('Renta', backref='sprinter', lazy=True)

class Renta(db.Model):
    __tablename__ = 'rentas'
    id_renta = db.Column(db.Integer, primary_key=True)
    id_cliente = db.Column(db.Integer, db.ForeignKey('clientes.id_cliente'))
    id_sprinter = db.Column(db.Integer, db.ForeignKey('sprinters.id_sprinter'))
    fecha_inicio = db.Column(db.Date)
    fecha_fin = db.Column(db.Date)
    costo = db.Column(db.Numeric(10,2))
