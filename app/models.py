from datetime import datetime, timezone
from decimal import Decimal

from flask_login import UserMixin
from werkzeug.security import check_password_hash, generate_password_hash

from app import db, login_manager


@login_manager.user_loader
def load_user(user_id):
    return db.session.get(Usuario, int(user_id))


class Usuario(UserMixin, db.Model):
    __tablename__ = "usuarios"

    id = db.Column(db.Integer, primary_key=True)
    nombre = db.Column(db.String(100), nullable=False)
    email = db.Column(db.String(150), unique=True, nullable=False, index=True)
    password_hash = db.Column(db.String(255), nullable=False)
    rol = db.Column(db.String(20), nullable=False, default="ventas")
    chofer_id = db.Column(db.Integer, db.ForeignKey("choferes.id"))
    cliente_id = db.Column(db.Integer, db.ForeignKey("clientes.id"))
    activo = db.Column(db.Boolean, nullable=False, default=True)
    fecha_registro = db.Column(
        db.DateTime, nullable=False, default=lambda: datetime.now(timezone.utc)
    )

    @property
    def is_active(self):
        return self.activo

    def set_password(self, password):
        self.password_hash = generate_password_hash(password)

    def check_password(self, password):
        return check_password_hash(self.password_hash, password)


class Cliente(db.Model):
    __tablename__ = "clientes"

    id = db.Column(db.Integer, primary_key=True)
    nombre = db.Column(db.String(100), nullable=False)
    telefono = db.Column(db.String(20), nullable=False)
    email = db.Column(db.String(150), nullable=False)
    rfc = db.Column(db.String(13))
    tipo_cliente = db.Column(db.String(20), nullable=False, default="particular")
    activo = db.Column(db.Boolean, nullable=False, default=True)
    reservas = db.relationship("Reserva", back_populates="cliente")


class Unidad(db.Model):
    __tablename__ = "unidades"

    id = db.Column(db.Integer, primary_key=True)
    codigo = db.Column(db.String(20), unique=True, nullable=False)
    marca = db.Column(db.String(50), nullable=False, default="Mercedes-Benz")
    modelo = db.Column(db.String(50), nullable=False, default="Sprinter")
    anio = db.Column(db.Integer, nullable=False)
    placas = db.Column(db.String(20), unique=True, nullable=False)
    capacidad_pasajeros = db.Column(db.Integer, nullable=False)
    estatus = db.Column(db.String(20), nullable=False, default="disponible")
    precio_dia = db.Column(db.Numeric(10, 2), nullable=False)
    fecha_compra = db.Column(db.Date)
    kilometraje = db.Column(db.Integer, nullable=False, default=0)
    reservas = db.relationship("Reserva", back_populates="unidad")


class Chofer(db.Model):
    __tablename__ = "choferes"

    id = db.Column(db.Integer, primary_key=True)
    nombre = db.Column(db.String(100), nullable=False)
    apellidos = db.Column(db.String(100), nullable=False)
    licencia = db.Column(db.String(30), unique=True, nullable=False)
    telefono = db.Column(db.String(20), nullable=False)
    disponibilidad = db.Column(db.String(20), nullable=False, default="disponible")
    tarifa_dia = db.Column(db.Numeric(10, 2), nullable=False)
    reservas = db.relationship("Reserva", back_populates="chofer")


class Reserva(db.Model):
    __tablename__ = "reservas"

    id = db.Column(db.Integer, primary_key=True)
    folio = db.Column(db.String(20), unique=True, nullable=False)
    cliente_id = db.Column(db.Integer, db.ForeignKey("clientes.id"), nullable=False)
    unidad_id = db.Column(db.Integer, db.ForeignKey("unidades.id"), nullable=False)
    chofer_id = db.Column(db.Integer, db.ForeignKey("choferes.id"), nullable=False)
    fecha_salida = db.Column(db.DateTime, nullable=False)
    fecha_regreso = db.Column(db.DateTime, nullable=False)
    origen = db.Column(db.String(200), nullable=False)
    destino = db.Column(db.String(200), nullable=False)
    estatus = db.Column(db.String(20), nullable=False, default="confirmada")
    precio_total = db.Column(db.Numeric(10, 2), nullable=False)
    notas = db.Column(db.Text)

    cliente = db.relationship("Cliente", back_populates="reservas")
    unidad = db.relationship("Unidad", back_populates="reservas")
    chofer = db.relationship("Chofer", back_populates="reservas")
    pagos = db.relationship("Pago", back_populates="reserva", cascade="all, delete-orphan")

    @property
    def saldo_pendiente(self):
        pagado = sum(
            (pago.monto for pago in self.pagos if pago.estatus == "pagado"),
            Decimal("0.00"),
        )
        return max(Decimal("0.00"), Decimal(self.precio_total) - pagado)


class Pago(db.Model):
    __tablename__ = "pagos"

    id = db.Column(db.Integer, primary_key=True)
    reserva_id = db.Column(db.Integer, db.ForeignKey("reservas.id"), nullable=False)
    monto = db.Column(db.Numeric(10, 2), nullable=False)
    fecha_pago = db.Column(
        db.DateTime, nullable=False, default=lambda: datetime.now(timezone.utc)
    )
    metodo_pago = db.Column(db.String(30), nullable=False)
    estatus = db.Column(db.String(20), nullable=False, default="pendiente")
    referencia = db.Column(db.String(100))

    reserva = db.relationship("Reserva", back_populates="pagos")
