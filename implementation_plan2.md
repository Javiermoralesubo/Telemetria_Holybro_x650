# Plan de Transformación Integral: Estación Terrena GCS de Alto Rendimiento (Pixhawk 6X)

Este plan detalla la modernización completa de la estación terrena para llevarla al **máximo nivel de ingeniería y desarrollo aeroespacial**. Incorpora gestión dinámica de puertos, instrumentos de vuelo PFD (Horizonte Artificial en Canvas), monitor de vibraciones y EKF, sintonizador de parámetros PID, reproductor de simulaciones/logs, telemetría de alta frecuencia y una interfaz gráfica premium de nivel profesional.

---

## 1. Arquitectura del Backend (`app.py`)

### 1.1 Administrador Dinámico de Conexiones
- **Escaneo Automático de Puertos**: Detección en vivo de puertos COM activos (Windows/Linux) y endpoints de simulación SITL (`udp:127.0.0.1:14550`, `tcp:127.0.0.1:5760`).
- **Conexión/Desconexión en Caliente**: Endpoints `/api/conectar`, `/api/desconectar` y `/api/listar_puertos` para cambiar de interfaz sin reiniciar el servidor.
- **Métricas de Enlace en Tiempo Real**: Cálculo de frecuencia efectiva de recepción (Hz), pérdida de paquetes (%) y tiempo de conexión activo.

### 1.2 Solicitud Proactiva de Streams MAVLink (High Rate Telemetry)
Se solicitarán flujos continuos a frecuencias óptimas mediante `request_data_stream_send` y `MAV_CMD_SET_MESSAGE_INTERVAL`:
- `ATTITUDE` / `HIGHRES_IMU` @ **20 Hz** (Dinámica y control).
- `VIBRATION` @ **10 Hz** (Vibraciones en X, Y, Z y conteo de clipping de acelerómetros).
- `EKF_STATUS_REPORT` @ **5 Hz** (Salud del filtro de estimación de estado).
- `VFR_HUD` / `GLOBAL_POSITION_INT` / `GPS_RAW_INT` @ **10 Hz** (Navegación y vuelo).
- `SYS_STATUS` / `BATTERY_STATUS` @ **2 Hz** (Energía, voltajes y salud de placa).
- `SERVO_OUTPUT_RAW` / `RC_CHANNELS` @ **10 Hz** (Monitoreo de actuadores y radio).
- `NAV_CONTROLLER_OUTPUT` @ **10 Hz** (Consignas y errores de guiado para ajuste de algoritmos).
- `STATUSTEXT` (Alertas nativas de PX4 y ArduPilot).

### 1.3 Suite de Comandos de Control y Seguridad
- **Armado / Desarmado Seguro**: Comando `MAV_CMD_COMPONENT_ARM_DISARM` con verificación previa.
- **Conmutación de Modos de Vuelo**: Soporte bidireccional PX4 / ArduPilot (MANUAL, STABILIZE, ALT_HOLD, POS_HOLD, RTL, LAND, OFFBOARD, GUIDED).
- **Parada de Emergencia**: Corte inmediato de actuadores.
- **Gestión de Parámetros MAVLink (PID Tuning)**: Lectura (`PARAM_REQUEST_READ`) y escritura (`PARAM_SET`) de ganancias y parámetros de control.

### 1.4 Modo Reproductor / Simulador Offline (CSV Playback)
- Capacidad de reproducir archivos CSV de telemetría grabados previamente ([telemetria_escritorio.csv](file:///c:/Users/calde/OneDrive/Desktop/Archivos_Proyecto/telemetria_escritorio.csv)) a velocidad ajustable (1x, 2x, 5x) para desarrollar y depurar la estación sin necesidad de tener el dron conectado físicamente.

---

## 2. Nueva Interfaz y Pestañas del Frontend (`templates/index.html`)

Se transformará la estación en una suite modular de **7 Pestañas Especializadas**:

### 🛩️ Pestaña 1: PFD & Dashboard Operativo
- **Horizonte Artificial Aeronáutico (PFD)** renderizado en HTML5 Canvas a 60 FPS:
  - Escala de cabeceo (*Pitch Ladder* -90° a +90°), indicador de alabeo (*Roll Arc*), cinta de rumbo (*Heading Tape*), velocímetro de cinta y altímetro con indicador de ascenso/descenso (*VSI*).
- **Mapa Geoespacial Táctico**: Marcador del dron con flecha de rumbo real, punto de inicio (HOME), estela de trayectoria continua y alternador automático entre mapa online y mosaicos locales offline ([static/tiles](file:///c:/Users/calde/OneDrive/Desktop/Archivos_Proyecto/static/tiles)).
- **Tarjetas de Telemetría Dinámicas** y **Mini Consola Rápida**.

### 📊 Pestaña 2: Diagnóstico Avanzado de Sensores & Vibraciones
- **Medidor de Vibraciones 3D (X, Y, Z)** con zonas de tolerancia (Normal < 30 m/s², Precaución 30-60 m/s², Crítico > 60 m/s²), esencial para balanceo de hélices y detección de resonancias mecánicas.
- **Salud del Filtro EKF**: Varianzas de velocidad, posición horizontal, posición vertical y brújula.
- **Monitoreo Detallado de Batería**: Estimación de voltaje por celda (para baterías 3S, 4S, 6S), corriente pico y consumo en mAh.
- **IMU Completa**: Aceleraciones en $m/s^2$, velocidades angulares en $rad/s$, magnetómetros en $Gauss$, presión barométrica y temperatura de sensores.

### ⚙️ Pestaña 3: Banco de Actuadores & Pruebas de Banco
- Sliders independientes para hasta 8 salidas de motor con selector de timeout y debounce.
- Control maestro unificado y botón de parada de emergencia instantánea.
- Monitor en vivo de las señales PWM reales de salida (1000 - 2000 $\mu s$) y barras de nivel de los 8 canales del receptor RC.

### 🎛️ Pestaña 4: Sintonizador de Parámetros & PID Tuning
- Editor interactivo para consultar y ajustar parámetros en caliente:
  - Tarjetas rápidas de ajuste PID (Ganancias P, I, D de Roll, Pitch, Yaw y Altitud).
  - Buscador universal de parámetros MAVLink con lectura y escritura directa al Pixhawk.

### 📈 Pestaña 5: Analizador de Datos & Gráficos Multivariable
- Gráfico dinámico configurable con selector multieje (permite comparar **Valor Deseado vs. Valor Medido**).
- Controles de pausa en vivo, selector de ventana de tiempo (10s, 30s, 60s, 120s) y exportación directa de instantáneas.
- Botón de descarga de logs CSV completos de la sesión.

### 💻 Pestaña 6: Consola MAVLink & Auditoría de Eventos
- Registro cronológico con coloreado según severidad (EMERGENCY, CRITICAL, ERROR, WARNING, NOTICE, INFO, DEBUG).
- Buscador y filtro rápido de mensajes.

### 📁 Pestaña 7: Simulador & Reproductor de Vuelo
- Selector de log CSV para reproducir misiones y sesiones de banco paso a paso.
- Barra de progreso interactiva con botones de Reproducir, Pausa y velocidad de reproducción (1x, 2x, 4x).

---

## 3. Cambios Propuestos en Archivos

### Backend
#### [MODIFY] [app.py](file:///c:/Users/calde/OneDrive/Desktop/Archivos_Proyecto/app.py)
- Añadir escaneo de puertos COM y soporte para endpoints UDP/TCP.
- Implementar peticiones activas de flujo MAVLink a alta frecuencia (20 Hz).
- Procesar mensajes adicionales: `VIBRATION`, `EKF_STATUS_REPORT`, `NAV_CONTROLLER_OUTPUT`, `COMMAND_ACK`, `PARAM_VALUE`.
- Añadir endpoints para conexión/desconexión dinámica, cambio de modos de vuelo, armado/desarmado, parámetros PID y modo simulación/playback.

### Frontend
#### [MODIFY] [templates/index.html](file:///c:/Users/calde/OneDrive/Desktop/Archivos_Proyecto/templates/index.html)
- Integrar el PFD (Primary Flight Display) en Canvas.
- Añadir el selector de conexión en el encabezado (Puerto, Baudios, Botón Conectar/Desconectar y Switch Modo Simulación).
- Implementar las 7 pestañas de monitoreo, diagnóstico, sintonización y simulación.
- Integrar la barra de estado de vibraciones y salud EKF.
- Añadir soporte para estela de vuelo en el mapa Leaflet y soporte offline transparente.

---

## 4. Plan de Verificación

### Verificación de Endpoints y Comunicación
- Comprobar que `/api/conexiones/puertos` liste los puertos locales y opciones UDP.
- Verificar que el hilo de telemetría procese los paquetes expandidos sin elevar el consumo de CPU.
- Probar el modo de simulación cargando [telemetria_escritorio.csv](file:///c:/Users/calde/OneDrive/Desktop/Archivos_Proyecto/telemetria_escritorio.csv) para validar el renderizado del PFD y gráficos sin necesidad de hardware conectado.

### Verificación de Interfaz de Usuario
- Validar que el Horizonte Artificial (PFD) reaccione con fluidez a los cambios de Pitch, Roll y Yaw.
- Probar la navegación entre las 7 pestañas asegurando que los gráficos, mapas y sliders no sufran desincronización.
- Comprobar la activación y seguridad del panel de motores y el sintonizador de parámetros.
