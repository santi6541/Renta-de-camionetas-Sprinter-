-- Esquema vigente del sistema; también está disponible en db/schema.sql.
-- Este script conserva las bases y tablas existentes.

CREATE DATABASE IF NOT EXISTS renta_sprinter
    CHARACTER SET utf8mb4
    COLLATE utf8mb4_unicode_ci;
USE renta_sprinter;

CREATE TABLE IF NOT EXISTS clientes (
    id INT AUTO_INCREMENT PRIMARY KEY,
    nombre VARCHAR(100) NOT NULL,
    telefono VARCHAR(20) NOT NULL,
    email VARCHAR(150) NOT NULL,
    rfc VARCHAR(13),
    tipo_cliente VARCHAR(20) NOT NULL DEFAULT 'particular',
    activo BOOLEAN NOT NULL DEFAULT TRUE
);

CREATE TABLE IF NOT EXISTS unidades (
    id INT AUTO_INCREMENT PRIMARY KEY,
    codigo VARCHAR(20) NOT NULL UNIQUE,
    marca VARCHAR(50) NOT NULL DEFAULT 'Mercedes-Benz',
    modelo VARCHAR(50) NOT NULL DEFAULT 'Sprinter',
    anio INT NOT NULL,
    placas VARCHAR(20) NOT NULL UNIQUE,
    capacidad_pasajeros INT NOT NULL,
    estatus VARCHAR(20) NOT NULL DEFAULT 'disponible',
    precio_dia DECIMAL(10, 2) NOT NULL,
    fecha_compra DATE,
    kilometraje INT NOT NULL DEFAULT 0
);

CREATE TABLE IF NOT EXISTS choferes (
    id INT AUTO_INCREMENT PRIMARY KEY,
    nombre VARCHAR(100) NOT NULL,
    apellidos VARCHAR(100) NOT NULL,
    licencia VARCHAR(30) NOT NULL UNIQUE,
    telefono VARCHAR(20) NOT NULL,
    disponibilidad VARCHAR(20) NOT NULL DEFAULT 'disponible',
    tarifa_dia DECIMAL(10, 2) NOT NULL
);

CREATE TABLE IF NOT EXISTS usuarios (
    id INT AUTO_INCREMENT PRIMARY KEY,
    nombre VARCHAR(100) NOT NULL,
    email VARCHAR(150) NOT NULL UNIQUE,
    password_hash VARCHAR(255) NOT NULL,
    rol VARCHAR(20) NOT NULL DEFAULT 'ventas',
    chofer_id INT,
    cliente_id INT,
    activo BOOLEAN NOT NULL DEFAULT TRUE,
    fecha_registro DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (chofer_id) REFERENCES choferes(id),
    FOREIGN KEY (cliente_id) REFERENCES clientes(id)
);

CREATE TABLE IF NOT EXISTS reservas (
    id INT AUTO_INCREMENT PRIMARY KEY,
    folio VARCHAR(20) NOT NULL UNIQUE,
    cliente_id INT NOT NULL,
    unidad_id INT NOT NULL,
    chofer_id INT NOT NULL,
    fecha_salida DATETIME NOT NULL,
    fecha_regreso DATETIME NOT NULL,
    origen VARCHAR(200) NOT NULL,
    destino VARCHAR(200) NOT NULL,
    estatus VARCHAR(20) NOT NULL DEFAULT 'confirmada',
    precio_total DECIMAL(10, 2) NOT NULL,
    notas TEXT,
    FOREIGN KEY (cliente_id) REFERENCES clientes(id),
    FOREIGN KEY (unidad_id) REFERENCES unidades(id),
    FOREIGN KEY (chofer_id) REFERENCES choferes(id),
    INDEX idx_reservas_fechas (fecha_salida, fecha_regreso),
    INDEX idx_reservas_estatus (estatus)
);

CREATE TABLE IF NOT EXISTS pagos (
    id INT AUTO_INCREMENT PRIMARY KEY,
    reserva_id INT NOT NULL,
    monto DECIMAL(10, 2) NOT NULL,
    fecha_pago DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    metodo_pago VARCHAR(30) NOT NULL,
    estatus VARCHAR(20) NOT NULL DEFAULT 'pendiente',
    referencia VARCHAR(100),
    FOREIGN KEY (reserva_id) REFERENCES reservas(id),
    INDEX idx_pagos_estatus_fecha (estatus, fecha_pago)
);
