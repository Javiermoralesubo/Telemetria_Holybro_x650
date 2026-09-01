# 🚀 Walkthrough: Estación Terrena de Control Aeroespacial (GCS Pixhawk 6X)

Se ha completado la **modernización y maximización integral** de la estación terrena ([app.py](file:///c:/Users/calde/OneDrive/Desktop/Archivos_Proyecto/app.py) y [templates/index.html](file:///c:/Users/calde/OneDrive/Desktop/Archivos_Proyecto/templates/index.html)), transformándola en una suite de control y diagnóstico de nivel profesional para desarrollo e investigación aeroespacial con Pixhawk 6X (PX4 y ArduPilot).

---

## 🌟 Resumen de Capacidades Implementadas

### 1. Conectividad Dinámica Universal y Alta Frecuencia (20 Hz)
- **Selector de Puertos en Vivo**: Escaneo automático de puertos COM locales (`COM1` a `COM24`), radio telemetría SiK y presets para simuladores SITL (`udp:127.0.0.1:14550`, `tcp:127.0.0.1:5760`).
- **Conexión / Desconexión en Caliente**: Botón interactivo para alternar conexiones sin reiniciar el script de Python.
- **Transmisión de Ultra-Baja Latencia**: Servidor SSE (Server-Sent Events) en `/api/stream` que entrega telemetría a **20 Hz** continuos.
- **Stream Scheduler MAVLink**: Envío proactivo de comandos `MAV_CMD_SET_MESSAGE_INTERVAL` y `request_data_stream_send` para recibir actitud, IMU, vibraciones, EKF y navegación a máxima tasa.

### 2. Instrumento de Vuelo PFD (Primary Flight Display) 60 FPS
- **Horizonte Artificial Aeronáutico** renderizado en HTML5 Canvas con aceleración por hardware:
  - *Pitch Ladder* dinámico con escala de -80° a +80°.
  - *Roll Arc* con puntero de alabeo e índices angulares.
  - Símbolo central de aeronave y división de cielo/tierra con gradiente.
  - Cinta de Rumbo (Heading Compass) superior con indicación digital.
  - Cinta vertical de Velocidad (m/s y km/h) a la izquierda.
  - Cinta vertical de Altitud (AGL) a la derecha con tasa de ascenso/descenso.

### 3. Suite Modular de 7 Pestañas de Diagnóstico y Control
1. **🛩️ PFD & Dashboard Operativo**:
   - PFD Horizonte Artificial.
   - Mapa geoespacial Leaflet con **estela de trayectoria continua (breadcrumb)**, seguimiento del dron y soporte offline garantizado con mosaicos locales ([static/tiles](file:///c:/Users/calde/OneDrive/Desktop/Archivos_Proyecto/static/tiles)).
   - Botonera rápida de modos de vuelo (`POSCTL`, `ALTCTL`, `STABILIZE`, `RTL`, `LAND`), Armado seguro y Parada de emergencia.
2. **📊 Diagnóstico de Sensores, IMU & Vibraciones (FFT)**:
   - Medidor de Vibraciones 3D ($Vibe_X, Vibe_Y, Vibe_Z$) con zonas de seguridad coloreadas (Normal < 30 m/s², Precaución 30-60 m/s², Crítico > 60 m/s²) y conteo de *Clipping*.
   - Diagnóstico del Estimador EKF (varianzas de velocidad, horizontal, vertical y brújula).
   - Datos crudos de IMU (acelerómetros, giroscopios, magnetómetros, presión y temperatura de placa).
   - Diagnóstico de energía con **voltaje estimado por celda (V/c)**, corriente y mAh consumidos.
3. **⚙️ Banco de Actuadores & Motores**:
   - Panel de control estilo QGroundControl para hasta 8 motores independientes con *Safety Toggle*, *debounce*, deslizador maestro y parada de emergencia instantánea (Tecla `Espacio`).
4. **🎛️ Sintonizador de Parámetros & Control PID**:
   - Tarjetas de ajuste rápido para ganancias P, I, D de Roll Rate, Pitch Rate, Yaw Rate y límites de velocidad (`MPC_XY_VEL_MAX`, etc.).
   - Inspector universal de parámetros MAVLink con lectura y escritura directa al Pixhawk.
5. **📈 Gráficos en Vivo & Análisis Multivariable**:
   - Gráfica Chart.js interactiva con selector de métricas (Actitud, Dinámica, Vibraciones 3D, Batería, IMU) y selector de ventana temporal (10s, 30s, 60s).
   - Botón para descargar el log CSV registrado.
6. **💻 Consola MAVLink & Eventos**:
   - Terminal en vivo con captura de mensajes `STATUSTEXT` emitidos por el Pixhawk clasificados por severidad (INFO, ADVERTENCIA, ERROR, CRÍTICO).
7. **📁 Reproductor de Logs / Simulador de Vuelo**:
   - Modo de simulación integrado que lee [telemetria_escritorio.csv](file:///c:/Users/calde/OneDrive/Desktop/Archivos_Proyecto/telemetria_escritorio.csv) para reproducir sesiones anteriores en banco con control de velocidad (0.5x, 1x, 2x, 4x), ideal para pruebas de laboratorio sin hardware conectado.

---

## 📋 Instrucciones de Uso

1. **Iniciar el servidor**:
   ```bash
   python app.py
   ```
2. **Abrir la Estación Terrena en el navegador**:
   - Navegar a `http://localhost:5000`
3. **Probar sin hardware (Modo Simulación)**:
   - Activar el interruptor **"Simulador CSV"** en la barra superior o en la pestaña **📁 Reproductor de Logs**. Verás el PFD, mapa, gráficos y telemetría cobrando vida en tiempo real.
4. **Conectar al Pixhawk real**:
   - Seleccionar el puerto (`COM7`, `COM3`, `udp:127.0.0.1:14550`, etc.) y hacer clic en **🔌 Conectar**.
