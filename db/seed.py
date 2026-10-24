from app import db
from app.models import Cliente, Chofer, Unidad


def seed_demo_data():
    if not Cliente.query.first():
        db.session.add_all(
            [
                Cliente(
                    nombre="Cliente de demostración",
                    telefono="555-0101",
                    email="cliente1@example.test",
                    tipo_cliente="particular",
                ),
                Cliente(
                    nombre="Empresa de demostración",
                    telefono="555-0102",
                    email="empresa@example.test",
                    tipo_cliente="empresa",
                ),
            ]
        )
    if not Unidad.query.first():
        db.session.add_all(
            [
                Unidad(
                    codigo="SP-001",
                    anio=2022,
                    placas="DEMO-01",
                    capacidad_pasajeros=15,
                    precio_dia=2500,
                    kilometraje=55000,
                ),
                Unidad(
                    codigo="SP-002",
                    anio=2021,
                    placas="DEMO-02",
                    capacidad_pasajeros=20,
                    precio_dia=3000,
                    kilometraje=89000,
                ),
            ]
        )
    if not Chofer.query.first():
        db.session.add_all(
            [
                Chofer(
                    nombre="Roberto",
                    apellidos="Gómez",
                    licencia="DEMO-LIC-01",
                    telefono="555-0201",
                    tarifa_dia=800,
                ),
                Chofer(
                    nombre="Sofía",
                    apellidos="Ramírez",
                    licencia="DEMO-LIC-02",
                    telefono="555-0202",
                    tarifa_dia=850,
                ),
            ]
        )
    db.session.commit()