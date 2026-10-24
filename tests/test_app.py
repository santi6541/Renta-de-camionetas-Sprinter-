import unittest
from datetime import datetime, timedelta

from app import create_app, db
from app.models import Cliente, Chofer, Pago, Reserva, Unidad, Usuario


class TestConfig:
    TESTING = True
    SECRET_KEY = "test-secret"
    SQLALCHEMY_DATABASE_URI = "sqlite://"
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    WTF_CSRF_ENABLED = False


class RentalAppTests(unittest.TestCase):
    def setUp(self):
        self.app = create_app(TestConfig)
        self.context = self.app.app_context()
        self.context.push()
        db.create_all()
        self.client = self.app.test_client()

        admin = Usuario(nombre="Admin", email="admin@example.test", rol="administrador")
        admin.set_password("correct-horse-battery")
        sales = Usuario(nombre="Ventas", email="ventas@example.test", rol="ventas")
        sales.set_password("correct-horse-battery")
        client_user = Usuario(nombre="Cliente", email="cliente@example.test", rol="cliente")
        client_user.set_password("correct-horse-battery")
        self.customer = Cliente(
            nombre="Cliente de prueba",
            telefono="555-0100",
            email="test@example.test",
        )
        self.unit = Unidad(
            codigo="SP-TEST",
            anio=2022,
            placas="TEST-01",
            capacidad_pasajeros=15,
            precio_dia=2500,
        )
        self.driver = Chofer(
            nombre="Chofer",
            apellidos="Prueba",
            licencia="TEST-LIC",
            telefono="555-0101",
            tarifa_dia=500,
        )
        db.session.add_all([admin, sales, client_user, self.customer, self.unit, self.driver])
        db.session.flush()
        client_user.cliente_id = self.customer.id
        db.session.commit()

    def tearDown(self):
        db.session.remove()
        db.drop_all()
        self.context.pop()

    def login(self, email):
        return self.client.post(
            "/auth/login",
            data={"email": email, "password": "correct-horse-battery"},
            follow_redirects=True,
        )

    def test_login_and_role_restrictions(self):
        response = self.client.get("/")
        self.assertEqual(response.status_code, 302)
        self.assertIn("/auth/login", response.headers["Location"])

        self.login("ventas@example.test")
        self.assertEqual(self.client.get("/clientes/").status_code, 200)
        self.assertEqual(self.client.get("/unidades/").status_code, 403)

    def test_admin_can_open_each_management_page(self):
        self.login("admin@example.test")
        for path in (
            "/dashboard",
            "/clientes/",
            "/clientes/nuevo",
            "/unidades/",
            "/unidades/nueva",
            "/choferes/",
            "/choferes/nuevo",
            "/reservas/",
            "/reservas/nueva",
            "/pagos/",
            "/pagos/nuevo",
            "/reportes/financiero",
            "/api/reservas",
        ):
            with self.subTest(path=path):
                self.assertEqual(self.client.get(path).status_code, 200)

    def test_admin_can_create_clients_units_and_drivers(self):
        self.login("admin@example.test")
        posts = (
            (
                "/clientes/nuevo",
                {
                    "nombre": "Nuevo cliente",
                    "telefono": "555-0110",
                    "email": "nuevo@example.test",
                    "rfc": "",
                    "tipo_cliente": "empresa",
                },
            ),
            (
                "/unidades/nueva",
                {
                    "codigo": "SP-NEW",
                    "marca": "Mercedes-Benz",
                    "modelo": "Sprinter",
                    "anio": "2023",
                    "placas": "NEW-01",
                    "capacidad_pasajeros": "18",
                    "estatus": "disponible",
                    "precio_dia": "2100.00",
                    "fecha_compra": "",
                    "kilometraje": "0",
                },
            ),
            (
                "/choferes/nuevo",
                {
                    "nombre": "Nuevo",
                    "apellidos": "Chofer",
                    "licencia": "NEW-LIC",
                    "telefono": "555-0111",
                    "disponibilidad": "disponible",
                    "tarifa_dia": "650.00",
                },
            ),
        )
        for path, data in posts:
            with self.subTest(path=path):
                self.assertEqual(
                    self.client.post(path, data=data, follow_redirects=True).status_code,
                    200,
                )
        self.assertEqual(Cliente.query.filter_by(email="nuevo@example.test").count(), 1)
        self.assertEqual(Unidad.query.filter_by(codigo="SP-NEW").count(), 1)
        self.assertEqual(Chofer.query.filter_by(licencia="NEW-LIC").count(), 1)

    def test_reservation_payment_and_excel_report(self):
        self.login("admin@example.test")
        start = (datetime.now() + timedelta(days=4)).replace(second=0, microsecond=0)
        end = start + timedelta(days=1)
        response = self.client.post(
            "/reservas/nueva",
            data={
                "cliente_id": str(self.customer.id),
                "unidad_id": str(self.unit.id),
                "chofer_id": str(self.driver.id),
                "fecha_salida": start.isoformat(timespec="minutes"),
                "fecha_regreso": end.isoformat(timespec="minutes"),
                "origen": "Ciudad de México",
                "destino": "Puebla",
                "estatus": "confirmada",
            },
            follow_redirects=True,
        )
        self.assertEqual(response.status_code, 200)
        reserva = Reserva.query.one()
        self.assertEqual(reserva.precio_total, 3000)

        conflict = self.client.post(
            "/reservas/nueva",
            data={
                "cliente_id": str(self.customer.id),
                "unidad_id": str(self.unit.id),
                "chofer_id": str(self.driver.id),
                "fecha_salida": start.isoformat(timespec="minutes"),
                "fecha_regreso": end.isoformat(timespec="minutes"),
                "origen": "Ciudad de México",
                "destino": "Puebla",
                "estatus": "confirmada",
            },
            follow_redirects=True,
        )
        self.assertIn("ya tiene una reserva", conflict.get_data(as_text=True))
        self.assertEqual(Reserva.query.count(), 1)

        response = self.client.post(
            "/pagos/nuevo",
            data={
                "reserva_id": str(reserva.id),
                "monto": "1000.00",
                "metodo_pago": "transferencia",
                "estatus": "pagado",
                "referencia": "TEST-001",
            },
            follow_redirects=True,
        )
        self.assertEqual(response.status_code, 200)
        self.assertEqual(Pago.query.one().estatus, "pagado")
        self.assertEqual(self.client.get("/reportes/financiero").status_code, 200)
        report = self.client.get("/reportes/exportar/excel")
        self.assertEqual(report.status_code, 200)
        self.assertIn(
            "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
            report.mimetype,
        )

    def test_customer_dashboard_only_shows_their_reservations(self):
        other = Cliente(
            nombre="Otro cliente",
            telefono="555-0999",
            email="otro@example.test",
        )
        other_reservation = Reserva(
            folio="OTHER-001",
            cliente=other,
            unidad=self.unit,
            chofer=self.driver,
            fecha_salida=datetime.now() + timedelta(days=10),
            fecha_regreso=datetime.now() + timedelta(days=11),
            origen="Origen",
            destino="Destino",
            precio_total=3000,
        )
        db.session.add(other_reservation)
        db.session.commit()
        self.login("cliente@example.test")
        response = self.client.get("/dashboard")
        self.assertEqual(response.status_code, 200)
        self.assertNotIn(b"Clientes activos", response.data)
        response = self.client.get("/mis-reservas")
        self.assertEqual(response.status_code, 200)
        self.assertNotIn(b"OTHER-001", response.data)


if __name__ == "__main__":
    unittest.main()
