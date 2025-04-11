-- Crear base de datos
CREATE DATABASE IF NOT EXISTS hotelera;
USE hotelera;

-- Tabla de hoteles
CREATE TABLE hotel (
    id_hotel INT AUTO_INCREMENT PRIMARY KEY,
    nombre VARCHAR(50) NOT NULL,
    direccion TEXT,
    telefono VARCHAR(15),
    email VARCHAR(50) UNIQUE,
    contrasenia VARCHAR(55),
    fecha_registro TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Tabla de usuarios
CREATE TABLE usuario (
    id_usuario INT AUTO_INCREMENT PRIMARY KEY,
    nombre_completo VARCHAR(255) NOT NULL,
    telefono VARCHAR(15),
    email VARCHAR(255) UNIQUE,
    numero_cedula VARCHAR(20),
    direccion TEXT,
    contrasenia VARCHAR(100),
    fecha_registro TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Tabla de empleados del hotel
CREATE TABLE empleado (
    id_empleado INT AUTO_INCREMENT PRIMARY KEY,
    id_hotel INT,
    nombre_completo VARCHAR(255) NOT NULL,
    email VARCHAR(255) UNIQUE,
    telefono VARCHAR(15),
    cargo VARCHAR(50),
    user_admin VARCHAR(50) UNIQUE,
    contrasenia_admin VARCHAR(100),
    FOREIGN KEY (id_hotel) REFERENCES hotel(id_hotel)
);

-- Tabla de habitaciones
CREATE TABLE habitacion (
    id_habitacion INT AUTO_INCREMENT PRIMARY KEY,
    id_hotel INT,
    numero VARCHAR(10),
    descripcion TEXT,
    precio_noche DECIMAL(10,2),
    tipo VARCHAR(50),
    estado VARCHAR(50),
    FOREIGN KEY (id_hotel) REFERENCES hotel(id_hotel)
);

-- Tabla de reservas
CREATE TABLE reserva (
    id_reserva INT AUTO_INCREMENT PRIMARY KEY,
    fecha_reserva TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    fecha_checkin DATE,
    fecha_checkout DATE,
    estado VARCHAR(50),
    metodo_pago VARCHAR(50),
    monto_total DECIMAL(10,2),
    id_usuario INT,
    id_empleado INT,
    id_hotel INT,
    FOREIGN KEY (id_usuario) REFERENCES usuario(id_usuario),
    FOREIGN KEY (id_empleado) REFERENCES empleado(id_empleado),
    FOREIGN KEY (id_hotel) REFERENCES hotel(id_hotel)
);

-- Tabla intermedia reserva-habitacion (muchos a muchos)
CREATE TABLE reserva_habitacion (
    id_reserva_habitacion INT AUTO_INCREMENT PRIMARY KEY,
    id_reserva INT,
    id_habitacion INT,
    FOREIGN KEY (id_reserva) REFERENCES reserva(id_reserva),
    FOREIGN KEY (id_habitacion) REFERENCES habitacion(id_habitacion)
);

-- Tabla comprobantes de pago
CREATE TABLE comprobante_pago (
    id_comprobante INT AUTO_INCREMENT PRIMARY KEY,
    id_reserva INT,
    archivo_comprobante VARCHAR(255),
    fecha_subida TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (id_reserva) REFERENCES reserva(id_reserva)
);

-- Tabla de reportes contables
CREATE TABLE reporte_contable (
    id_reporte INT AUTO_INCREMENT PRIMARY KEY,
    generado_por INT,
    fecha_generacion TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    archivo_excel VARCHAR(255),
    FOREIGN KEY (generado_por) REFERENCES empleado(id_empleado)
);

CREATE VIEW vista_reservas_detalladas AS
SELECT
    r.id_reserva,
    u.nombre_completo AS cliente,
    h.nombre AS hotel,
    r.fecha_checkin,
    r.fecha_checkout,
    r.estado,
    r.metodo_pago,
    r.monto_total
FROM reserva r
JOIN usuario u ON r.id_usuario = u.id_usuario
JOIN hotel h ON r.id_hotel = h.id_hotel;

DELIMITER //
CREATE TRIGGER before_insert_reserva
BEFORE INSERT ON reserva
FOR EACH ROW
BEGIN
    IF NEW.estado IS NULL THEN
        SET NEW.estado = 'Pendiente';
    END IF;
END;
//
DELIMITER ;

