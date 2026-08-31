# Plan de Implementación: Visualización Completa de Telemetría y Sistema de Pestañas MAVLink

Este plan describe la ampliación del backend (`app.py`) y del frontend (`templates/index.html`) para capturar, procesar y visualizar todos los paquetes de telemetría MAVLink emitidos por el Pixhawk 6X, organizando la estación terrena en un sistema de pestañas modular, intuitivo y moderno.

---

## 1. Captura de Telemetría Completa en Backend (`app.py`)

Actualmente, el hilo de telemetría solo captura paquetes de tipo `ATTITUDE`. Se modificará el ciclo de lectura para procesar todos los mensajes recibidos mediante `conexion.recv_msg()` y solicitar flujos de datos (`request_data_stream_send` / `MAV_CMD_SET_MESSAGE_INTERVAL`):

### Mensajes MAVLink a Procesar:
1. **`ATTITUDE`**:
   - `pitch`, `roll`, `yaw`, `pitchspeed`, `rollspeed`, `yawspeed` (radianes y grados).
2. **`VFR_HUD`**:
   - `airspeed` (velocidad aire), `groundspeed` (velocidad tierra), `heading` (rumbo en grados), `throttle` (% acelerador), `alt` (altitud barométrica), `climb` (tasa de ascenso m/s).
3. **`GLOBAL_POSITION_INT` / `GPS_RAW_INT`**:
   - `lat`, `lon` (coordenadas GPS en grados decimales), `alt` (altitud AMSL), `relative_alt` (altitud relativa sobre el despegue), `vx`, `vy`, `vz` (velocidades NED), `fix_type` (tipo de fijación GPS), `satellites_visible` (número de satélites visibles), `eph` (HDOP).
4. **`SYS_STATUS` / `BATTERY_STATUS`**:
   - `voltage_battery` (voltaje en V), `current_battery` (corriente en A), `battery_remaining` (% restante), `load` (carga de CPU en %), `drop_rate_comm` (% pérdida de paquetes).
5. **`HEARTBEAT`**:
   - `autopilot`, `base_mode`, `custom_mode` (modo de vuelo decodificado: MANUAL, STABILIZED, POSCTL, ALTCTL, OFFBOARD, etc.), `system_status`, estado de armado (`armed` / `disarmed`).
6. **`HIGHRES_IMU` / `RAW_IMU`**:
   - Acelerómetro X, Y, Z ($m/s^2$ o $mg$), Giroscopio X, Y, Z ($rad/s$), Magnetómetro X, Y, Z ($Gauss$), `temperature` (°C), `abs_pressure` ($hPa$).
7. **`SERVO_OUTPUT_RAW` / `ACTUATOR_OUTPUT_STATUS`**:
   - Señales PWM reales de salida para Motor 1, 2, 3, 4, etc. ($1000 - 2000 \mu s$).
8. **`RC_CHANNELS`**:
   - Canales de control de radio (CH1 - CH8) y calidad de enlace `rssi`.
9. **`STATUSTEXT`**:
   - Mensajes y alertas nativas emitidas por el Pixhawk (PX4 / ArduPilot).

### Endpoints REST / API:
- `GET /api/datos`: Retorna el estado consolidado de todos los subsistemas de telemetría en formato JSON estructurado.
- `GET /api/descargar_log`: Permite descargar el archivo CSV de telemetría registrado.
- `POST /api/motor/<id>/<valor>` y `POST /api/motor/stop_all`: Control de motores MAVLink ya operativo.

---

## 2. Nueva Arquitectura de Pestañas en Frontend (`templates/index.html`)

Se implementará una barra de navegación superior con pestañas reactivas e independientes:

### Pestaña 1: 📊 **Dashboard Principal (Visión General)**
- **Tarjetas de Estado Rápido**: Batería %, Modo de Vuelo, Estado Armado/Disarmed, Altitud Relativa, Velocidad Terrestre, Satélites GPS, Tiempo de Vuelo.
- **Instrumentos de Vuelo**: Horizonte artificial / Indicador de actitud visual (Pitch/Roll/Yaw), Rumbo/Brújula.
- **Radar Local & Mapa Geoespacial interactivo** con seguimiento dinámico del dron vía GPS.
- **Gráfico en tiempo real** de Actitud y Altitud.

### Pestaña 2: 📋 **Telemetría Completa (Sensores & Subsistemas)**
- Cuadrícula de monitores en vivo organizados por módulos:
  1. **Navegación & Posición**: Lat, Lon, Altitud AMSL, Altitud Relativa, Velocidad 3D ($V_x, V_y, V_z$), Heading, HDOP, Satélites.
  2. **Energía & Sistema**: Voltaje total, Corriente instantánea, Consumo acumulado, % Batería, Carga de CPU, Temperatura de placa.
  3. **IMU & Sensores Inerciales**: Aceleración ($a_x, a_y, a_z$), Velocidad angular ($\omega_x, \omega_y, \omega_z$), Campo magnético ($m_x, m_y, m_z$), Presión barométrica.
  4. **Actuadores & Canales de Entrada**: Salidas Servo/Motor (PWM $\mu s$) y Canales del receptor RC (CH1-CH8) con barras de nivel.

### Pestaña 3: ⚙️ **Prueba de Actuadores (Motores)**
- El panel de Actuator Testing estilo QGroundControl:
  - Interruptor de seguridad *Safety Toggle*.
  - Deslizadores individuales con debounce independiente (Motores 1 a 4).
  - Deslizador maestro *Todos los Motores*.
  - Botón de parada de emergencia general.
  - Monitor en tiempo real del comando MAVLink transmitido.

### Pestaña 4: 📈 **Gráficos & Análisis en Tiempo Real**
- Selector multivariable para graficar: Actitud, Altitud/Velocidad, Batería/Corriente, Aceleraciones IMU.
- Botón para descargar el log CSV de la sesión actual.

### Pestaña 5: 💻 **Consola MAVLink & Eventos**
- Registro en vivo con filtro de severidad para capturar mensajes de texto del Pixhawk (`STATUSTEXT`) y auditoría de comandos enviados.

---

## 3. Plan de Verificación

### Verificación de Servidor y Endpoints
- Validar sintaxis y compilación: `python -m py_compile app.py`.
- Probar endpoint `/api/datos` con la estructura de datos expandida.
- Probar endpoint `/api/descargar_log` para asegurar la descarga del CSV.

### Verificación en Navegador
- Navegar entre las 5 pestañas comprobando que no haya parpadeos ni pérdidas de datos en los gráficos o sliders.
- Verificar que las actualizaciones de telemetría en vivo a 5Hz-10Hz funcionen de manera fluida.
- Comprobar que los sliders de la pestaña de Actuadores sigan enviando los comandos MAVLink correctamente.
