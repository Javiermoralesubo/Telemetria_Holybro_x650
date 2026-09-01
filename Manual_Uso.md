# 🚁 Manual de Uso - Estación Terrena GCS (Pixhawk 6X & Flask)

Estación Terrena de Control en Tiempo Real (Ground Control Station - GCS) desarrollada para la telemetría, planificación de misiones y diagnóstico de drones **Holybro X650** equipados con **Pixhawk 6X**, **PX4 / ArduPilot**, **Python (Flask)**, **pymavlink** y **Chart.js / Leaflet.js**.

---

## 🚀 Características Principales

* **Telemetría en Vivo 20 Hz:** Lectura en tiempo real de actitud (Pitch, Roll, Yaw), velocidad, altitud AGL, estado de batería por celda, varianza EKF y vibraciones 3D.
* **Planificador de Misiones & Setpoints (Estilo QGroundControl):** Creación interactiva de rutas haciendo clic sobre el mapa, asignación de altitudes y velocidades, subida directa al Pixhawk vía MAVLink e importación/exportación de archivos `.plan` de QGroundControl.
* **Selección Libre de Puertos COM & Web Serial API:** Menú desplegable con entrada manual libre (`COM1` a `COM256`, `/dev/ttyUSB0`) y detección nativa por navegador mediante Web Serial API.
* **Primary Flight Display (PFD) 60 FPS:** Horizonte artificial aeronáutico en HTML5 Canvas con cintas de rumbo, altitud y velocidad.
* **Gráficos Dinámicos Continuos:** Historial de telemetría a 60 FPS con ventanas ajustables (10s, 30s, 60s, 120s, 300s o Historial Completo sin cortes).
* **Control de Actuadores (Sliders de Motores):** Panel interactivo de pruebas de motores adaptado para el firmware PX4 / ArduPilot con parada de emergencia instantánea (Tecla `Espacio`).
* **Sintonizador PID:** Modificación y lectura de parámetros de control en vivo guardando directamente en la memoria flash del autopiloto.
* **Simulador CSV Integrado:** Reproducción de vuelos grabados paso a paso con control de velocidad (0.5x, 1x, 2x, 4x).

---

## 🛠️ Tecnologías Utilizadas

* **Backend:** Python 3.10+, Flask, PyMAVLink, PySerial
* **Frontend:** HTML5, CSS3 Glassmorphism, JavaScript (ES6)
* **Librerías de Visualización:** Chart.js v4.5.1, Leaflet.js v1.9.4
* **Hardware:** Holybro Pixhawk 6X (PX4 / ArduPilot) & Holybro X650 Quadcopter

---

## 🔌 Conexión del Hardware y Selección de Puertos

1. Conecta tu **Pixhawk 6X** o radio módem SiK al computador mediante USB o telemetría 915 MHz / 433 MHz.
2. Inicia la aplicación y abre `http://localhost:5000`.
3. En la barra superior de conexión:
   - Selecciona tu puerto en el menú desplegable (ej. `COM7`, `COM3`, `COM4`).
   - Si tu puerto no aparece listado, elige **`✏️ Otro / Escribir puerto...`** y escribe directamente el puerto asignado (ej: `COM8`, `COM12`, `/dev/ttyUSB0`).
   - También puedes presionar el botón **`🔌 Web Serial`** para que tu navegador detecte y vincule el puerto COM USB automáticamente.
4. Selecciona los baudios (habitualmente `57600` para radio o `115200` / `921600` para USB) y haz clic en **`🔌 Conectar`**.

---

## 🗺️ Guía del Planificador de Misiones (Setpoints)

1. Dirígete a la pestaña **`🗺️ Planificador de Misión (Setpoints)`**.
2. **Agregar Setpoints**: Haz clic en cualquier ubicación del mapa para agregar waypoints numerados (`WP1`, `WP2`, `WP3`...).
3. **Modificar Parámetros**: En la tabla derecha, puedes cambiar el tipo de comando (`TAKEOFF`, `WAYPOINT`, `LOITER`, `RTL`, `LAND`) y la altitud objetivo en metros.
4. **Reordenar / Arrastrar**: Arrastra directamente los marcadores en el mapa para ajustar coordenadas o usa los botones `⬆️` / `⬇️` en la tabla.
5. **Enviar al Dron**: Haz clic en **`🚀 Enviar al Dron`** para transmitir la misión al Pixhawk vía MAVLink.
6. **Ejecutar Misión**: Presiona **`▶ Iniciar (AUTO)`** para cambiar el modo del dron a `AUTO` y comenzar la ruta.
7. **Integración con QGroundControl**: Usa **`💾 Exportar QGC .plan`** o **`📂 Importar QGC`** para compartir misiones con QGroundControl.

---

## ⚠️ Advertencia de Seguridad Crítica

* Si vas a realizar pruebas en el **Banco de Actuadores (Motores)**, **retira las hélices físicamente** del dron para evitar accidentes.
* Presiona la tecla **`Espacio`** en cualquier momento para activar la parada de emergencia instantánea.

---

## 🚀 Subir Cambios a GitHub

Para respaldar tu código en GitHub, simplemente haz doble clic en el archivo **`push_to_github.bat`**. El script detectará Git, creará el commit y subirá los cambios a tu repositorio automáticamente.
