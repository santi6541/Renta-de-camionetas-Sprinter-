-- Crear base de datos y tablas
DROP DATABASE IF EXISTS renta_sprinter;
CREATE DATABASE renta_sprinter;
USE renta_sprinter;

CREATE TABLE clientes (
    id_cliente INT AUTO_INCREMENT PRIMARY KEY,
    nombre VARCHAR(100) NOT NULL,
    telefono VARCHAR(20),
    correo VARCHAR(100)
);

CREATE TABLE sprinters (
    id_sprinter INT AUTO_INCREMENT PRIMARY KEY,
    modelo VARCHAR(50) NOT NULL,
    placas VARCHAR(20) NOT NULL,
    disponible BOOLEAN DEFAULT TRUE
);

CREATE TABLE rentas (
    id_renta INT AUTO_INCREMENT PRIMARY KEY,
    id_cliente INT,
    id_sprinter INT,
    fecha_inicio DATE,
    fecha_fin DATE,
    costo DECIMAL(10,2),
    FOREIGN KEY (id_cliente) REFERENCES clientes(id_cliente),
    FOREIGN KEY (id_sprinter) REFERENCES sprinters(id_sprinter)
);

-- Datos de ejemplo
INSERT INTO clientes (nombre, telefono, correo) VALUES
('Juan Pérez', '555-1234', 'juanperez@mail.com'),
('Ana López', '555-5678', 'ana@mail.com');

INSERT INTO sprinters (modelo, placas, disponible) VALUES
('Mercedes Sprinter 2020', 'ABC-123', TRUE),
('Mercedes Sprinter 2019', 'XYZ-456', TRUE);

INSERT INTO rentas (id_cliente, id_sprinter, fecha_inicio, fecha_fin, costo) VALUES
(1, 1, '2025-08-01', '2025-08-05', 5000.00),
(2, 2, '2025-08-10', '2025-08-12', 2500.00);
