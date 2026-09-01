# Plan de Implementación: Planificador de Rutas de Vuelo (Setpoints & QGroundControl)

Este plan añade un **Módulo de Planificación de Misiones y Rutas de Vuelo interactivas basado en Setpoints/Waypoints**, con soporte bidireccional para exportar e importar archivos `.plan` compatibles con **QGroundControl** y cargar la misión directamente al autopiloto Pixhawk a través del protocolo MAVLink.

## User Review Required

> [!IMPORTANT]
> Se añadirá la pestaña **🗺️ Planificador de Misión (Setpoints)** en la barra principal del GCS. El usuario podrá hacer clic en el mapa geoespacial táctico para definir waypoints, ajustar sus altitudes y velocidades, sincronizar la misión con el dron a través de MAVLink y exportar/importar proyectos en formato oficial QGroundControl `.plan`.

## Open Questions

Ninguna. La estructura de mensajes MAVLink `MISSION_ITEM_INT` / `MISSION_COUNT` y la especificación `.plan` de QGroundControl son estándar para PX4 y ArduPilot.

## Proposed Changes

### Backend (Python - Flask & PyMAVLink)

#### [MODIFY] [app.py](file:///c:/Users/alumno/Desktop/Telemetria_Holybro_x650-main/Telemetria_Holybro_x650-main/app.py)

- **Gestión de Estado de Misión**:
  - Declarar variable global `mision_actual` para almacenar la lista de setpoints (Latitud, Longitud, Altitud, Tipo de comando, Velocidad, Demora).
- **Rutas API de Misión**:
  - `GET /api/mision`: Obtener la lista de setpoints de la misión actual.
  - `POST /api/mision/guardar`: Guardar y actualizar los setpoints en el backend.
  - `POST /api/mision/subir`: Transmitir los waypoints de la misión al Pixhawk/Autopiloto vía protocolo MAVLink (`MISSION_CLEAR_ALL`, `MISSION_COUNT`, `MISSION_ITEM_INT`).
  - `GET /api/mision/descargar`: Solicitar y recuperar los waypoints almacenados en la memoria del Pixhawk.
  - `POST /api/mision/exportar_qgc`: Generar y enviar el archivo estructurado JSON `.plan` compatible con QGroundControl.
  - `POST /api/mision/importar_qgc`: Recibir y parsear un archivo `.plan` o `.waypoints` de QGroundControl y convertirlo en la ruta de setpoints activa.

---

### Frontend (HTML / JavaScript / CSS)

#### [MODIFY] [index.html](file:///c:/Users/alumno/Desktop/Telemetria_Holybro_x650-main/Telemetria_Holybro_x650-main/templates/index.html)

- **Pestaña 8: 🗺️ Planificador de Misión (Setpoints)**:
  - Añadir botón de navegación en la barra principal (`nav-tabs`).
  - Diseñar el layout responsivo dividido en **Mapa Interactivo de Ruta** y **Tabla de Setpoints**:
    - **Mapa Leaflet de Planificación**: Permite agregar waypoints haciendo clic directo sobre el mapa, visualizar marcadores numerados (`WP1`, `WP2`, `WP3`...), trazar la polilínea de vuelo y arrastrar marcadores para ajustar coordenadas.
    - **Barra de Herramientas de Misión**:
      - Switch de Modo Edición / Inserción.
      - Parámetros por defecto (Altitud de despegue/crucero, Velocidad).
      - Métricas en tiempo real: Distancia total de la ruta (metros/km), Número de Setpoints, Tiempo estimado de vuelo.
      - Botones de acción: `🚀 Enviar Misión a Pixhawk`, `📥 Descargar de Pixhawk`, `▶ Iniciar Misión (Modo AUTO)`, `💾 Exportar QGC .plan`, `📂 Importar QGC .plan`, `🗑️ Limpiar Ruta`.
    - **Tabla Táctica de Setpoints**: Permite modificar la altitud, velocidad, tipo de acción (`TAKEOFF`, `WAYPOINT`, `LOITER`, `RTL`, `LAND`), reordenar puntos o eliminarlos individualmente.

## Verification Plan

### Automated Tests / Scripts
- Verificar la construcción de estructuras `.plan` de QGroundControl mediante pruebas de serialización/deserialización JSON.

### Manual Verification
1. Abrir la nueva pestaña **🗺️ Planificador de Misión** en la interfaz web.
2. Hacer clic en varios puntos del mapa para trazar una ruta con 4 o más setpoints (`TAKEOFF` -> `WAYPOINT` -> `WAYPOINT` -> `RTL`).
3. Modificar la altitud de un setpoint en la tabla y verificar que el mapa actualice el pop-up e información.
4. Exportar la misión como archivo `.plan` de QGroundControl y reimportarla para verificar la integridad de los datos.
5. Hacer clic en `🚀 Enviar Misión al Dron` con el simulador o Pixhawk conectado y verificar la respuesta MAVLink.
