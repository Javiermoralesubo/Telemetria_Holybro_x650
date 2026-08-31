# 🚁 Estación Terrena GCS (Pixhawk 6X & Flask)

Estación Terrena de Control en Tiempo Real (Ground Control Station - GCS) desarrollada en modo escritorio como parte de un proyecto de telemetría y control de drones utilizando **Pixhawk 6X**, **PX4**, **Python (Flask)** y **pymavlink**.

---

## 🚀 Características Principales
* **Telemetría en Vivo:** Lectura en tiempo real de los datos de actitud de la IMU (Pitch, Roll, Yaw) mediante MAVLink.
* **Interfaz Web Moderna:** Dashboard oscuro de alto rendimiento con diseño industrial estilo GCS profesional y marcas de agua institucionales.
* **Radar NED local y Mapa Geoespacial:** Integración con Leaflet y Canvas para posicionamiento georreferenciado y visualización vectorial.
* **Gráficos Dinámicos:** Historial de comportamiento en vivo utilizando `Chart.js` con métricas intercambiables.
* **Registro Automático:** Guardado de datos de vuelo en formato `.csv` en tiempo real.
* **Control de Actuadores (Sliders de Motores):** Panel interactivo de pruebas de motores adaptado para el firmware PX4.

---

## 🛠️ Tecnologías Utilizadas
* **Backend:** Python, Flask, PyMavlink
* **Frontend:** HTML5, CSS3, JavaScript
* **Librerías de Visualización:** Chart.js, Leaflet.js
* **Hardware:** Pixhawk 6X (Firmware PX4 1.17.0)

---

## 📂 2. Estructura del Proyecto

Asegúrate de que tus archivos estén organizados de la siguiente manera en tu computador para que Flask pueda encontrarlos sin errores:

```text
mi_proyecto_gcs/
│
├── static/
│   └── logo_ubo.png          <-- Logotipo institucional
│
├── templates/
│   └── index.html            <-- Interfaz gráfica del dashboard
│
├── app.py                    <-- Servidor principal de Python
└── requirements.txt          <-- Lista de dependencias
```

---

## 📋 3. Requisitos Previos e Instalación

1. **Python** (versión 3.8 o superior instalado en tu sistema).
2. Abre la terminal Powershell y ejecuta el siguiente comando:
   ````bash
   pip install pyserial
   ````
4. Las librerías necesarias del proyecto. Abre tu terminal (CMD o PowerShell) en la carpeta del proyecto y ejecuta:

```bash
pip install -r requirements.txt
```
*(Contenido del archivo `requirements.txt`: Flask==3.0.2, pymavlink==2.4.38, pyserial==3.5)*

---

## 🔌 4. Conexión del Hardware y Seguridad

1. Conecta tu **Pixhawk 6X** al computador mediante un cable USB.
2. Identifica en qué puerto serie está conectada (por ejemplo, `COM8` en Windows). Si tu puerto es diferente, abre el archivo `app.py` con un editor de texto y cambia la línea de configuración:
   ```python
   PUERTO_CONEXION = "COM8"  # Cambia por tu puerto actual (ej: COM3, COM4, etc.)
   ```
3. **⚠️ ADVERTENCIA DE SEGURIDAD CRÍTICA:** 
   * Si vas a realizar pruebas con los deslizadores de motores, **quita las hélices físicamente** del dron para evitar accidentes.
   * Conecta la batería LiPo principal (el USB solo alimenta el procesador).
   * Asegúrate de que el botón de seguridad físico tenga la luz LED fija.
   * En la configuración de PX4, verifica que el parámetro `COM_MOT_TEST_EN` esté establecido en `1`.

---

## 🚀 5. Ejecución del Sistema

Sigue estos pasos en orden para encender tu estación terrena:

1. **Cierra completamente QGroundControl** u otros software de telemetría (para evitar conflictos de puertos en el puerto serie COM).
2. Abre tu terminal (PowerShell o CMD) y navega hasta la carpeta del proyecto.
3. Ejecuta el servidor de Python con el siguiente comando:
   ```bash
   python app.py
   ```
4. Verás en la consola un mensaje indicando que se ha conectado a la Pixhawk de forma exitosa.
5. Abre tu navegador web favorito (Chrome, Edge, etc.) y escribe la siguiente dirección:
   ```text
   http://127.0.0.1:5000
   ```
6. ¡Listo! Visualizarás tu panel de control con la telemetría en vivo, mapas, gráficos de actitud y los controles deslizantes de motores.
