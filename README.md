# 🚁 Estación Terrena GCS (Pixhawk 6X & Flask)

Estación Terrena de Control en Tiempo Real (Ground Control Station - GCS) desarrollada para modo escritorio como parte de un proyecto de telemetría y control de drones utilizando **Pixhawk 6X**, **PX4**, **Python (Flask)** y **pymavlink**.

## 🚀 Características Principales
* **Telemetría en Vivo:** Lectura en tiempo real de los datos de actitud de la IMU (Pitch, Roll, Yaw) mediante MAVLink.
* **Interfaz Web Moderna:** Dashboard oscuro de alto rendimiento con diseño industrial estilo GCS profesional.
* **Radar NED local y Mapa Geoespacial:** Integración con Leaflet y Canvas para posicionamiento georreferenciado y visualización vectorial.
* **Gráficos Dinámicos:** Historial de comportamiento en vivo utilizando `Chart.js`.
* **Registro Automático:** Guardado de datos de vuelo en formato `.csv` en tiempo real.
* **Prueba de Actuadores (Actuator Testing):** Panel de control interactivo para verificación de motores mediante comandos MAVLink.

## 🛠️ Tecnologías Utilizadas
* **Backend:** Python, Flask, PyMavlink
* **Frontend:** HTML5, CSS3, JavaScript
* **Librerías de Visualización:** Chart.js, Leaflet.js
* **Hardware:** Pixhawk 6X (Firmware PX4)

## 📦 Instalación y Uso

1. Clona este repositorio:
   ```bash
   git clone [https://github.com/tu-usuario/tu-repositorio.git](https://github.com/tu-usuario/tu-repositorio.git)
   cd tu-repositorio
