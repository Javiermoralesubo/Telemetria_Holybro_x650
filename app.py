import time
import math
import csv
import threading
import logging
import json
import os
from flask import Flask, render_template, jsonify, request, send_file, Response
from pymavlink import mavutil

# Desactivar logs internos redundantes de Flask
log = logging.getLogger('werkzeug')
log.setLevel(logging.ERROR)

app = Flask(__name__)

# --- CONFIGURACIÓN POR DEFECTO ---
ARCHIVO_LOG_ACTUAL = "telemetria_escritorio.csv"
PUERTO_DEFECTO = "COM7"
BAUD_DEFECTO = 57600

# Constantes de comandos MAVLink
MAV_CMD_DO_MOTOR_TEST = 209          # Comando estándar clásico / ArduPilot
MAV_CMD_ACTUATOR_TEST = 310          # Comando estándar moderno PX4 (Pixhawk 6X / QGC)
MAV_CMD_COMPONENT_ARM_DISARM = 400   # Armar/Desarmar
MAV_CMD_DO_SET_MODE = 176            # Cambiar modo de vuelo clásico
MAV_CMD_SET_MESSAGE_INTERVAL = 511   # Solicitar tasa específica por mensaje
MOTOR_TEST_THROTTLE_PERCENT = 0      # Tipo de acelerador 0: porcentaje (0 - 100)

# Control de Hilos y Conexión
grabando_telemetria = True
hilo_receptor_activo = True
conexion = None
conexion_lock = threading.Lock()
hilo_telemetria = None

# Configuración activa de conexión
config_conexion = {
    "puerto": PUERTO_DEFECTO,
    "baud": BAUD_DEFECTO,
    "tipo": "serial",
    "conectado": False,
    "estado_texto": "Desconectado",
    "paquetes_totales": 0,
    "hz_actual": 0.0,
    "perdida_paquetes_pct": 0.0,
    "modo_simulacion": False
}

def limpiar_float(val, default=0.0):
    """Limpia valores flotantes evitando NaN o Inf para JSON estricto"""
    if val is None:
        return default
    try:
        f = float(val)
        if math.isnan(f) or math.isinf(f):
            return default
        return round(f, 3)
    except (ValueError, TypeError):
        return default

# Estructura de Telemetría Completa y Consolidada de Grado Aeroespacial
telemetria_actual = {
    "conectado": False,
    "tiempo": 0.0,
    "hz_recepcion": 0.0,
    "pitch": 0.0,
    "roll": 0.0,
    "yaw": 0.0,
    "conexion": {
        "puerto": PUERTO_DEFECTO,
        "baud": BAUD_DEFECTO,
        "conectado": False,
        "estado": "Desconectado",
        "paquetes_recibidos": 0,
        "hz": 0.0,
        "simulacion": False
    },
    "sistema": {
        "modo_vuelo": "DESCONOCIDO",
        "armado": False,
        "tipo_autopilot": "PX4",
        "carga_cpu": 0.0,
        "perdida_com": 0.0,
        "voltaje_bateria": 0.0,
        "corriente_bateria": 0.0,
        "bateria_pct": 0,
        "mah_consumidos": 0.0,
        "voltaje_celda": 0.0,
        "temperatura_placa": 0.0
    },
    "actitud": {
        "pitch": 0.0,
        "roll": 0.0,
        "yaw": 0.0,
        "pitch_deg": 0.0,
        "roll_deg": 0.0,
        "yaw_deg": 0.0,
        "pitchspeed": 0.0,
        "rollspeed": 0.0,
        "yawspeed": 0.0
    },
    "vfr_hud": {
        "airspeed": 0.0,
        "groundspeed": 0.0,
        "altitud_baro": 0.0,
        "climb": 0.0,
        "heading": 0,
        "throttle": 0
    },
    "gps": {
        "fix_type": 0,
        "fix_desc": "Sin GPS (Interiores)",
        "lat": -33.467225,
        "lon": -70.657605,
        "alt_amsl": 0.0,
        "alt_rel": 0.0,
        "satellites": 0,
        "hdop": 99.9,
        "vx": 0.0,
        "vy": 0.0,
        "vz": 0.0
    },
    "imu": {
        "acc_x": 0.0,
        "acc_y": 0.0,
        "acc_z": 0.0,
        "gyro_x": 0.0,
        "gyro_y": 0.0,
        "gyro_z": 0.0,
        "mag_x": 0.0,
        "mag_y": 0.0,
        "mag_z": 0.0,
        "presion_hpa": 1013.25,
        "temp_sensor": 25.0
    },
    "vibracion": {
        "vibe_x": 0.0,
        "vibe_y": 0.0,
        "vibe_z": 0.0,
        "clip_0": 0,
        "clip_1": 0,
        "clip_2": 0,
        "nivel_salud": "Excelente"
    },
    "ekf": {
        "flags": 0,
        "velocity_variance": 0.0,
        "pos_horiz_variance": 0.0,
        "pos_vert_variance": 0.0,
        "compass_variance": 0.0,
        "terrain_alt_variance": 0.0,
        "salud_ekf": "Normal"
    },
    "control_guiado": {
        "nav_pitch": 0.0,
        "nav_roll": 0.0,
        "nav_bearing": 0,
        "target_bearing": 0,
        "wp_dist": 0.0,
        "alt_error": 0.0,
        "aspd_error": 0.0,
        "xtrack_error": 0.0
    },
    "actuadores": {
        "motor1_pwm": 1000,
        "motor2_pwm": 1000,
        "motor3_pwm": 1000,
        "motor4_pwm": 1000,
        "motor5_pwm": 1000,
        "motor6_pwm": 1000,
        "motor7_pwm": 1000,
        "motor8_pwm": 1000
    },
    "rc": {
        "ch1": 1500, "ch2": 1500, "ch3": 1000, "ch4": 1500,
        "ch5": 1000, "ch6": 1000, "ch7": 1000, "ch8": 1000,
        "rssi": 0
    },
    "parametros": {
        "MC_ROLLRATE_P": 0.15,
        "MC_ROLLRATE_I": 0.20,
        "MC_ROLLRATE_D": 0.003,
        "MC_PITCHRATE_P": 0.15,
        "MC_PITCHRATE_I": 0.20,
        "MC_PITCHRATE_D": 0.003,
        "MC_YAWRATE_P": 0.20,
        "MC_YAWRATE_I": 0.10,
        "MC_YAWRATE_D": 0.000,
        "MPC_XY_VEL_MAX": 12.0,
        "MPC_Z_VEL_MAX_UP": 3.0,
        "MPC_Z_VEL_MAX_DN": 1.5
    },
    "mensajes_estado": [],
    "simulador": {
        "activo": False,
        "indice": 0,
        "total": 0,
        "velocidad": 1.0,
        "archivo": ARCHIVO_LOG_ACTUAL
    }
}

# --- DETECCIÓN DE PUERTOS SERIALES Y ENDPOINTS ---
def listar_puertos():
    """Detecta puertos COM disponibles en Windows y puertos tty en Linux"""
    puertos = []
    
    # 1. Intentar con pyserial si está disponible
    try:
        import serial.tools.list_ports
        for p in serial.tools.list_ports.comports():
            desc = f"{p.device} ({p.description})" if p.description else p.device
            puertos.append({"id": p.device, "nombre": desc, "tipo": "serial"})
    except Exception:
        pass

    # 2. Fallback de escaneo básico para Windows si no se detectaron
    if not puertos and os.name == 'nt':
        try:
            import serial
            for i in range(1, 25):
                port_name = f"COM{i}"
                try:
                    s = serial.Serial(port_name)
                    s.close()
                    puertos.append({"id": port_name, "nombre": f"{port_name} (Detectado)", "tipo": "serial"})
                except Exception:
                    pass
        except Exception:
            pass

    # 3. Añadir opciones fijas de simulación SITL y Telemetría IP
    puertos_fijos = [
        {"id": "COM7", "nombre": "COM7 (Pixhawk USB / Telemetría)", "tipo": "serial"},
        {"id": "COM3", "nombre": "COM3 (Pixhawk alternativo)", "tipo": "serial"},
        {"id": "COM4", "nombre": "COM4 (Radio Telemetría SiK)", "tipo": "serial"},
        {"id": "udp:127.0.0.1:14550", "nombre": "UDP 127.0.0.1:14550 (SITL / jMAVSim / Gazebo)", "tipo": "udp"},
        {"id": "udp:0.0.0.0:14550", "nombre": "UDP 0.0.0.0:14550 (Escucha GCS / Wi-Fi)", "tipo": "udp"},
        {"id": "tcp:127.0.0.1:5760", "nombre": "TCP 127.0.0.1:5760 (SITL TCP)", "tipo": "tcp"}
    ]
    
    ids_existentes = {p["id"] for p in puertos}
    for pf in puertos_fijos:
        if pf["id"] not in ids_existentes:
            puertos.append(pf)
            
    return puertos


# --- DECODIFICACIÓN DE MODOS DE VUELO ---
def decodificar_modo_vuelo(msg):
    """Decodifica el modo de vuelo para PX4 y ArduPilot desde el mensaje HEARTBEAT"""
    custom_mode = msg.custom_mode
    autopilot = msg.autopilot
    
    # PX4 Autopilot
    if autopilot == mavutil.mavlink.MAV_AUTOPILOT_PX4:
        main_mode = (custom_mode >> 16) & 0xFF
        sub_mode = (custom_mode >> 24) & 0xFF
        
        px4_modes = {
            1: "MANUAL",
            2: "ALTCTL (Alt. Hold)",
            3: "POSCTL (Pos. Hold)",
            4: "AUTO",
            5: "ACRO",
            6: "OFFBOARD",
            7: "STABILIZED",
            8: "RATTITUDE"
        }
        
        px4_auto_submodes = {
            1: "AUTO - READY",
            2: "AUTO - TAKEOFF",
            3: "AUTO - LOITER",
            4: "AUTO - MISSION",
            5: "AUTO - RTL",
            6: "AUTO - LAND",
            7: "AUTO - RTGS",
            8: "AUTO - FOLLOW ME",
            9: "AUTO - PRECLAND"
        }
        
        if main_mode == 4 and sub_mode in px4_auto_submodes:
            return px4_auto_submodes[sub_mode]
        return px4_modes.get(main_mode, f"PX4 ({main_mode})")
        
    # ArduPilot
    elif autopilot == mavutil.mavlink.MAV_AUTOPILOT_ARDUPILOTMEGA:
        ardu_copter_modes = {
            0: "STABILIZE", 1: "ACRO", 2: "ALT_HOLD", 3: "AUTO", 4: "GUIDED",
            5: "LOITER", 6: "RTL", 7: "CIRCLE", 9: "LAND", 11: "DRIFT",
            13: "SPORT", 14: "FLIP", 15: "AUTOTUNE", 16: "POSHOLD",
            17: "BRAKE", 18: "THROW", 19: "AVOID_ADSB", 20: "GUIDED_NOGPS"
        }
        return ardu_copter_modes.get(custom_mode, f"Ardu ({custom_mode})")
        
    return f"Modo {custom_mode}"


# --- SOLICITUD ACTIVA DE STREAMS MAVLINK (STREAM SCHEDULER) ---
def configurar_frecuencias_mavlink(conn):
    """Solicita activamente streams a alta frecuencia al Pixhawk"""
    if conn is None:
        return
    try:
        target_sys = conn.target_system if conn.target_system > 0 else 1
        target_comp = conn.target_component if conn.target_component > 0 else mavutil.mavlink.MAV_COMP_ID_AUTOPILOT1
        
        # 1. Solicitud clásica de Data Streams
        streams = [
            (mavutil.mavlink.MAV_DATA_STREAM_EXTRA1, 20),  # Attitude, IMU
            (mavutil.mavlink.MAV_DATA_STREAM_EXTRA2, 10),  # VFR_HUD
            (mavutil.mavlink.MAV_DATA_STREAM_POSITION, 10),# GPS, Global position
            (mavutil.mavlink.MAV_DATA_STREAM_EXTENDED_STATUS, 5), # Battery, System
            (mavutil.mavlink.MAV_DATA_STREAM_RAW_CONTROLLER, 10),# Servo outputs, RC
            (mavutil.mavlink.MAV_DATA_STREAM_RAW_SENSORS, 20)    # Raw IMU, Pressure
        ]
        
        for stream_id, rate in streams:
            conn.mav.request_data_stream_send(
                target_sys, target_comp,
                stream_id, rate, 1
            )
            time.sleep(0.01)

        # 2. Solicitud por ID de mensaje específico (MAV_CMD_SET_MESSAGE_INTERVAL)
        # Intervalo en microsegundos: 20Hz = 50000us, 10Hz = 100000us
        mensajes_clave = [
            (30, 50000),   # ATTITUDE (20 Hz)
            (74, 100000),  # VFR_HUD (10 Hz)
            (33, 100000),  # GLOBAL_POSITION_INT (10 Hz)
            (105, 50000),  # HIGHRES_IMU (20 Hz)
            (241, 100000), # VIBRATION (10 Hz)
            (193, 200000), # EKF_STATUS_REPORT (5 Hz)
            (36, 100000),  # SERVO_OUTPUT_RAW (10 Hz)
            (65, 200000)   # RC_CHANNELS (5 Hz)
        ]
        
        for msg_id, interval_us in mensajes_clave:
            conn.mav.command_long_send(
                target_sys, target_comp,
                MAV_CMD_SET_MESSAGE_INTERVAL,
                0,
                msg_id,
                interval_us,
                0, 0, 0, 0, 0
            )
            time.sleep(0.01)
            
        print("[MAVLink] Streams de alta frecuencia solicitados exitosamente (20Hz/10Hz).")
    except Exception as e:
        print(f"[MAVLink] Advertencia configurando streams: {e}")


# --- COMANDOS DE VUELO Y SEGURIDAD ---
def cambiar_modo_vuelo_cmd(modo_solicitado):
    """Envía comando MAVLink para cambiar el modo de vuelo"""
    global conexion
    if conexion is None:
        return False, "Pixhawk no conectado."
    
    modo = modo_solicitado.upper().strip()
    target_sys = conexion.target_system if conexion.target_system > 0 else 1
    target_comp = conexion.target_component if conexion.target_component > 0 else mavutil.mavlink.MAV_COMP_ID_AUTOPILOT1

    with conexion_lock:
        try:
            es_px4 = telemetria_actual["sistema"]["tipo_autopilot"] == "PX4"

            if es_px4:
                px4_map = {
                    "MANUAL": (1, 0),
                    "ALTCTL": (2, 0),
                    "ALT_HOLD": (2, 0),
                    "POSCTL": (3, 0),
                    "POS_HOLD": (3, 0),
                    "ACRO": (5, 0),
                    "OFFBOARD": (6, 0),
                    "STABILIZED": (7, 0),
                    "AUTO_RTL": (4, 5),
                    "RTL": (4, 5),
                    "AUTO_LAND": (4, 6),
                    "LAND": (4, 6),
                    "AUTO_TAKEOFF": (4, 2),
                    "AUTO_MISSION": (4, 4),
                    "AUTO_LOITER": (4, 3)
                }
                
                if modo in px4_map:
                    main_mode, sub_mode = px4_map[modo]
                    custom_mode = (main_mode << 16) | (sub_mode << 24)
                    conexion.mav.command_long_send(
                        target_sys, target_comp,
                        MAV_CMD_DO_SET_MODE,
                        0,
                        mavutil.mavlink.MAV_MODE_FLAG_CUSTOM_MODE_ENABLED,
                        custom_mode,
                        0, 0, 0, 0, 0
                    )
                    return True, f"Modo PX4 cambiado a: {modo}"
            else:
                ardu_map = {
                    "STABILIZE": 0, "ACRO": 1, "ALT_HOLD": 2, "AUTO": 3,
                    "GUIDED": 4, "LOITER": 5, "RTL": 6, "LAND": 9, "POSHOLD": 16
                }
                if modo in ardu_map:
                    custom_mode = ardu_map[modo]
                    conexion.mav.command_long_send(
                        target_sys, target_comp,
                        MAV_CMD_DO_SET_MODE,
                        0,
                        mavutil.mavlink.MAV_MODE_FLAG_CUSTOM_MODE_ENABLED,
                        custom_mode,
                        0, 0, 0, 0, 0
                    )
                    return True, f"Modo ArduPilot cambiado a: {modo}"
                    
            return False, f"Modo {modo} no reconocido para el autopiloto actual."
        except Exception as e:
            return False, f"Error al cambiar modo: {e}"


def armar_desarmar_cmd(armar=True, force=False):
    """Envía comando para armar o desarmar los motores"""
    global conexion
    if conexion is None:
        return False, "Pixhawk no conectado."
        
    with conexion_lock:
        try:
            target_sys = conexion.target_system if conexion.target_system > 0 else 1
            target_comp = conexion.target_component if conexion.target_component > 0 else mavutil.mavlink.MAV_COMP_ID_AUTOPILOT1
            
            param1 = 1.0 if armar else 0.0
            param2 = 21196.0 if force else 0.0
            
            conexion.mav.command_long_send(
                target_sys, target_comp,
                MAV_CMD_COMPONENT_ARM_DISARM,
                0,
                param1,
                param2,
                0, 0, 0, 0, 0
            )
            estado_txt = "ARMADO" if armar else "DESARMADO"
            return True, f"Comando transmitido: {estado_txt} (Pixhawk confirmando...)"
        except Exception as e:
            return False, f"Error al transmitir comando de armado: {e}"


def enviar_comando_motor(motor_id, valor_porcentaje, timeout_s=3.0):
    """Prueba de motor MAVLink compatible con PX4 (310) y ArduPilot (209)"""
    global conexion
    if conexion is None:
        return False, "Pixhawk no conectado."

    try:
        motor_id = int(motor_id)
        valor_porcentaje = float(valor_porcentaje)
    except (ValueError, TypeError):
        return False, "Parámetros de motor inválidos."

    with conexion_lock:
        try:
            target_system = conexion.target_system if conexion.target_system > 0 else 1
            target_component = conexion.target_component if conexion.target_component > 0 else mavutil.mavlink.MAV_COMP_ID_AUTOPILOT1

            if valor_porcentaje <= 0:
                # 1. PX4: Liberar actuador
                conexion.mav.command_long_send(
                    target_system, target_component,
                    MAV_CMD_ACTUATOR_TEST,
                    0, -1.0, 0.0, 0, 0, motor_id, 0, 0
                )
                # 2. ArduPilot: 0%
                conexion.mav.command_long_send(
                    target_system, target_component,
                    MAV_CMD_DO_MOTOR_TEST,
                    0, motor_id, MOTOR_TEST_THROTTLE_PERCENT, 0, 0, 0, 0, 0
                )
                return True, f"Motor {motor_id} detenido (0%)."
            else:
                val_px4 = min(max(valor_porcentaje / 100.0, 0.0), 1.0)
                # 1. PX4
                conexion.mav.command_long_send(
                    target_system, target_component,
                    MAV_CMD_ACTUATOR_TEST,
                    0, val_px4, float(timeout_s), 0, 0, motor_id, 0, 0
                )
                # 2. ArduPilot
                conexion.mav.command_long_send(
                    target_system, target_component,
                    MAV_CMD_DO_MOTOR_TEST,
                    0, motor_id, MOTOR_TEST_THROTTLE_PERCENT, float(valor_porcentaje), float(timeout_s), 0, 0, 0
                )
                return True, f"Motor {motor_id} activado al {valor_porcentaje}% ({timeout_s}s)."
        except Exception as e:
            return False, f"Error al transmitir comando MAVLink: {e}"


# --- GESTIÓN DE PARÁMETROS MAVLINK ---
def leer_parametro_mavlink(param_nombre):
    """Solicita la lectura de un parámetro al Pixhawk"""
    global conexion
    if conexion is None:
        return False, "Pixhawk no conectado."
    with conexion_lock:
        try:
            target_sys = conexion.target_system if conexion.target_system > 0 else 1
            target_comp = conexion.target_component if conexion.target_component > 0 else mavutil.mavlink.MAV_COMP_ID_AUTOPILOT1
            param_bytes = param_nombre.encode('ascii')[:16]
            conexion.mav.param_request_read_send(target_sys, target_comp, param_bytes, -1)
            return True, f"Solicitud de parámetro {param_nombre} enviada."
        except Exception as e:
            return False, str(e)


def escribir_parametro_mavlink(param_nombre, valor):
    """Escribe un valor de parámetro en el Pixhawk"""
    global conexion
    if conexion is None:
        return False, "Pixhawk no conectado."
    try:
        val_flt = float(valor)
    except ValueError:
        return False, "Valor numérico requerido."
        
    with conexion_lock:
        try:
            target_sys = conexion.target_system if conexion.target_system > 0 else 1
            target_comp = conexion.target_component if conexion.target_component > 0 else mavutil.mavlink.MAV_COMP_ID_AUTOPILOT1
            param_bytes = param_nombre.encode('ascii')[:16]
            conexion.mav.param_set_send(target_sys, target_comp, param_bytes, val_flt, mavutil.mavlink.MAV_PARAM_TYPE_REAL32)
            telemetria_actual["parametros"][param_nombre] = val_flt
            return True, f"Parámetro {param_nombre} establecido en {val_flt}."
        except Exception as e:
            return False, str(e)


# --- HILO RECEPTOR DE TELEMETRÍA MULTI-MENSAJE MAVLINK ---
def receptor_mavlink_worker():
    global grabando_telemetria, telemetria_actual, conexion, config_conexion, hilo_receptor_activo
    
    ultimo_mensaje_tiempo = time.time()
    ultimo_print_tiempo = time.time()
    ultimo_calculo_hz = time.time()
    contador_paquetes = 0
    start_time = time.time()
    
    while hilo_receptor_activo:
        try:
            if config_conexion["modo_simulacion"]:
                time.sleep(0.1)
                continue

            puerto_actual = config_conexion["puerto"]
            baud_actual = config_conexion["baud"]

            if conexion is None and config_conexion.get("deseado_conectar", True):
                print(f"[Telemetría] Intentando conectar a Pixhawk en {puerto_actual} ({baud_actual} baud)...")
                config_conexion["estado_texto"] = f"Conectando a {puerto_actual}..."
                
                try:
                    if puerto_actual.startswith("udp:") or puerto_actual.startswith("tcp:"):
                        nueva_conn = mavutil.mavlink_connection(puerto_actual, autoreconnect=True)
                    else:
                        nueva_conn = mavutil.mavserial(puerto_actual, baud=baud_actual, autoreconnect=True)
                        
                    with conexion_lock:
                        conexion = nueva_conn
                        
                    start_time = time.time()
                    ultimo_mensaje_tiempo = time.time()
                    config_conexion["conectado"] = True
                    config_conexion["estado_texto"] = f"Conectado ({puerto_actual})"
                    print(f"[Telemetría] Conexión establecida en {puerto_actual}.")
                    
                    # Solicitar streams a alta velocidad
                    threading.Thread(target=configurar_frecuencias_mavlink, args=(nueva_conn,), daemon=True).start()
                    
                except Exception as err_conn:
                    config_conexion["conectado"] = False
                    config_conexion["estado_texto"] = f"Error: {err_conn}"
                    time.sleep(2.5)
                    continue

            # Registro en archivo CSV
            with open(ARCHIVO_LOG_ACTUAL, mode='a', newline='') as file:
                writer = csv.writer(file)
                if file.tell() == 0:
                    writer.writerow([
                        "Tiempo(s)", "Pitch(rad)", "Roll(rad)", "Yaw(rad)", 
                        "AltRel(m)", "Groundspeed(m/s)", "Voltaje(V)", "Corriente(A)", "Bateria(%)",
                        "Latitud", "Longitud", "Satellites", "ModoVuelo", "VibeX", "VibeY", "VibeZ"
                    ])
                
                while hilo_receptor_activo and conexion is not None and not config_conexion["modo_simulacion"]:
                    msg = conexion.recv_match(blocking=True, timeout=0.04)
                    
                    if msg is not None:
                        tipo = msg.get_type()
                        tiempo_actual = round(time.time() - start_time, 2)
                        contador_paquetes += 1
                        config_conexion["paquetes_totales"] += 1
                        
                        telemetria_actual["tiempo"] = tiempo_actual
                        telemetria_actual["conectado"] = True
                        telemetria_actual["conexion"]["conectado"] = True
                        telemetria_actual["conexion"]["puerto"] = config_conexion["puerto"]
                        telemetria_actual["conexion"]["baud"] = config_conexion["baud"]
                        telemetria_actual["conexion"]["paquetes_recibidos"] = config_conexion["paquetes_totales"]
                        ultimo_mensaje_tiempo = time.time()

                        # Cálculo de frecuencia efectiva (Hz)
                        if time.time() - ultimo_calculo_hz >= 1.0:
                            delta_t = time.time() - ultimo_calculo_hz
                            hz = round(contador_paquetes / delta_t, 1)
                            telemetria_actual["hz_recepcion"] = hz
                            telemetria_actual["conexion"]["hz"] = hz
                            config_conexion["hz_actual"] = hz
                            contador_paquetes = 0
                            ultimo_calculo_hz = time.time()

                        # --- DECODIFICACIÓN POR MENSAJE ---
                        if tipo == 'ATTITUDE':
                            pitch = limpiar_float(msg.pitch)
                            roll = limpiar_float(msg.roll)
                            yaw = limpiar_float(msg.yaw)
                            
                            telemetria_actual["actitud"]["pitch"] = pitch
                            telemetria_actual["actitud"]["roll"] = roll
                            telemetria_actual["actitud"]["yaw"] = yaw
                            telemetria_actual["actitud"]["pitch_deg"] = round(math.degrees(pitch), 1)
                            telemetria_actual["actitud"]["roll_deg"] = round(math.degrees(roll), 1)
                            telemetria_actual["actitud"]["yaw_deg"] = round((math.degrees(yaw) + 360) % 360, 1)
                            telemetria_actual["actitud"]["pitchspeed"] = limpiar_float(msg.pitchspeed)
                            telemetria_actual["actitud"]["rollspeed"] = limpiar_float(msg.rollspeed)
                            telemetria_actual["actitud"]["yawspeed"] = limpiar_float(msg.yawspeed)

                            telemetria_actual["pitch"] = pitch
                            telemetria_actual["roll"] = roll
                            telemetria_actual["yaw"] = yaw

                            writer.writerow([
                                tiempo_actual, pitch, roll, yaw,
                                telemetria_actual["gps"]["alt_rel"],
                                telemetria_actual["vfr_hud"]["groundspeed"],
                                telemetria_actual["sistema"]["voltaje_bateria"],
                                telemetria_actual["sistema"]["corriente_bateria"],
                                telemetria_actual["sistema"]["bateria_pct"],
                                telemetria_actual["gps"]["lat"],
                                telemetria_actual["gps"]["lon"],
                                telemetria_actual["gps"]["satellites"],
                                telemetria_actual["sistema"]["modo_vuelo"],
                                telemetria_actual["vibracion"]["vibe_x"],
                                telemetria_actual["vibracion"]["vibe_y"],
                                telemetria_actual["vibracion"]["vibe_z"]
                            ])
                            file.flush()

                        elif tipo == 'VFR_HUD':
                            telemetria_actual["vfr_hud"]["airspeed"] = limpiar_float(msg.airspeed, 0.0)
                            telemetria_actual["vfr_hud"]["groundspeed"] = limpiar_float(msg.groundspeed, 0.0)
                            telemetria_actual["vfr_hud"]["altitud_baro"] = limpiar_float(msg.alt, 0.0)
                            telemetria_actual["vfr_hud"]["climb"] = limpiar_float(msg.climb, 0.0)
                            telemetria_actual["vfr_hud"]["heading"] = int(msg.heading) if hasattr(msg, 'heading') else 0
                            telemetria_actual["vfr_hud"]["throttle"] = int(msg.throttle) if hasattr(msg, 'throttle') else 0

                        elif tipo == 'ALTITUDE':
                            telemetria_actual["gps"]["alt_amsl"] = limpiar_float(msg.altitude_amsl, 0.0)
                            telemetria_actual["gps"]["alt_rel"] = limpiar_float(msg.altitude_relative, 0.0)

                        elif tipo == 'GLOBAL_POSITION_INT':
                            telemetria_actual["gps"]["lat"] = round(msg.lat / 1e7, 7)
                            telemetria_actual["gps"]["lon"] = round(msg.lon / 1e7, 7)
                            telemetria_actual["gps"]["alt_amsl"] = round(msg.alt / 1000.0, 2)
                            telemetria_actual["gps"]["alt_rel"] = round(msg.relative_alt / 1000.0, 2)
                            telemetria_actual["gps"]["vx"] = round(msg.vx / 100.0, 2)
                            telemetria_actual["gps"]["vy"] = round(msg.vy / 100.0, 2)
                            telemetria_actual["gps"]["vz"] = round(msg.vz / 100.0, 2)

                        elif tipo == 'GPS_RAW_INT':
                            telemetria_actual["gps"]["fix_type"] = msg.fix_type
                            fix_map = {0: "Sin GPS (Interiores)", 1: "Sin Fix", 2: "2D Fix", 3: "3D Fix", 4: "DGPS", 5: "RTK Float", 6: "RTK Fixed"}
                            telemetria_actual["gps"]["fix_desc"] = fix_map.get(msg.fix_type, f"Fix {msg.fix_type}")
                            telemetria_actual["gps"]["satellites"] = msg.satellites_visible
                            telemetria_actual["gps"]["hdop"] = round(msg.eph / 100.0 if hasattr(msg, 'eph') else 99.9, 2)
                            if msg.fix_type >= 2 and msg.lat != 0:
                                telemetria_actual["gps"]["lat"] = round(msg.lat / 1e7, 7)
                                telemetria_actual["gps"]["lon"] = round(msg.lon / 1e7, 7)

                        elif tipo == 'VIBRATION':
                            v_x = limpiar_float(msg.vibration_x)
                            v_y = limpiar_float(msg.vibration_y)
                            v_z = limpiar_float(msg.vibration_z)
                            telemetria_actual["vibracion"]["vibe_x"] = v_x
                            telemetria_actual["vibracion"]["vibe_y"] = v_y
                            telemetria_actual["vibracion"]["vibe_z"] = v_z
                            telemetria_actual["vibracion"]["clip_0"] = msg.clipping_0
                            telemetria_actual["vibracion"]["clip_1"] = msg.clipping_1
                            telemetria_actual["vibracion"]["clip_2"] = msg.clipping_2
                            
                            max_vibe = max(v_x, v_y, v_z)
                            if max_vibe < 30:
                                telemetria_actual["vibracion"]["nivel_salud"] = "Excelente (<30 m/s²)"
                            elif max_vibe < 60:
                                telemetria_actual["vibracion"]["nivel_salud"] = "Precaución (30-60 m/s²)"
                            else:
                                telemetria_actual["vibracion"]["nivel_salud"] = "Crítico (>60 m/s²)"

                        elif tipo == 'EKF_STATUS_REPORT':
                            telemetria_actual["ekf"]["flags"] = msg.flags
                            telemetria_actual["ekf"]["velocity_variance"] = limpiar_float(msg.velocity_variance)
                            telemetria_actual["ekf"]["pos_horiz_variance"] = limpiar_float(msg.pos_horiz_variance)
                            telemetria_actual["ekf"]["pos_vert_variance"] = limpiar_float(msg.pos_vert_variance)
                            telemetria_actual["ekf"]["compass_variance"] = limpiar_float(msg.compass_variance)
                            telemetria_actual["ekf"]["terrain_alt_variance"] = limpiar_float(msg.terrain_alt_variance)
                            max_var = max(msg.velocity_variance, msg.pos_horiz_variance, msg.pos_vert_variance, msg.compass_variance)
                            telemetria_actual["ekf"]["salud_ekf"] = "Óptimo" if max_var < 0.5 else ("Advertencia" if max_var < 1.0 else "Fallo EKF")

                        elif tipo == 'NAV_CONTROLLER_OUTPUT':
                            telemetria_actual["control_guiado"]["nav_pitch"] = limpiar_float(msg.nav_pitch)
                            telemetria_actual["control_guiado"]["nav_roll"] = limpiar_float(msg.nav_roll)
                            telemetria_actual["control_guiado"]["nav_bearing"] = int(msg.nav_bearing)
                            telemetria_actual["control_guiado"]["target_bearing"] = int(msg.target_bearing)
                            telemetria_actual["control_guiado"]["wp_dist"] = int(msg.wp_dist)
                            telemetria_actual["control_guiado"]["alt_error"] = limpiar_float(msg.alt_error)
                            telemetria_actual["control_guiado"]["aspd_error"] = limpiar_float(msg.aspd_error)
                            telemetria_actual["control_guiado"]["xtrack_error"] = limpiar_float(msg.xtrack_error)

                        elif tipo == 'SYS_STATUS':
                            v_bat = msg.voltage_battery
                            if v_bat == 65535 or v_bat <= 0:
                                telemetria_actual["sistema"]["voltaje_bateria"] = 5.0
                                telemetria_actual["sistema"]["voltaje_celda"] = 3.8
                            else:
                                v_tot = round(v_bat / 1000.0, 2)
                                telemetria_actual["sistema"]["voltaje_bateria"] = v_tot
                                celdas = 6 if v_tot > 18.0 else (4 if v_tot > 13.0 else (3 if v_tot > 8.0 else 1))
                                telemetria_actual["sistema"]["voltaje_celda"] = round(v_tot / celdas, 2)

                            telemetria_actual["sistema"]["corriente_bateria"] = round(msg.current_battery / 100.0, 2) if msg.current_battery >= 0 else 0.0
                            telemetria_actual["sistema"]["bateria_pct"] = msg.battery_remaining if msg.battery_remaining >= 0 else 100
                            telemetria_actual["sistema"]["carga_cpu"] = round(msg.load / 10.0, 1)
                            telemetria_actual["sistema"]["perdida_com"] = round(msg.drop_rate_comm / 100.0, 1) if hasattr(msg, 'drop_rate_comm') else 0.0

                        elif tipo == 'BATTERY_STATUS':
                            if msg.battery_remaining >= 0:
                                telemetria_actual["sistema"]["bateria_pct"] = msg.battery_remaining
                            if msg.current_battery >= 0:
                                telemetria_actual["sistema"]["corriente_bateria"] = round(msg.current_battery / 100.0, 2)
                            if hasattr(msg, 'current_consumed') and msg.current_consumed >= 0:
                                telemetria_actual["sistema"]["mah_consumidos"] = msg.current_consumed

                        elif tipo == 'HEARTBEAT':
                            telemetria_actual["sistema"]["armado"] = bool(msg.base_mode & mavutil.mavlink.MAV_MODE_FLAG_SAFETY_ARMED)
                            telemetria_actual["sistema"]["modo_vuelo"] = decodificar_modo_vuelo(msg)
                            telemetria_actual["sistema"]["tipo_autopilot"] = "PX4" if msg.autopilot == mavutil.mavlink.MAV_AUTOPILOT_PX4 else "ArduPilot"

                        elif tipo == 'SCALED_PRESSURE':
                            telemetria_actual["imu"]["presion_hpa"] = limpiar_float(msg.press_abs, 1013.2)
                            telemetria_actual["sistema"]["temperatura_placa"] = limpiar_float(msg.temperature / 100.0 if hasattr(msg, 'temperature') else 25.0, 25.0)

                        elif tipo in ('HIGHRES_IMU', 'RAW_IMU'):
                            if tipo == 'HIGHRES_IMU':
                                telemetria_actual["imu"]["acc_x"] = limpiar_float(msg.xacc)
                                telemetria_actual["imu"]["acc_y"] = limpiar_float(msg.yacc)
                                telemetria_actual["imu"]["acc_z"] = limpiar_float(msg.zacc)
                                telemetria_actual["imu"]["gyro_x"] = limpiar_float(msg.xgyro)
                                telemetria_actual["imu"]["gyro_y"] = limpiar_float(msg.ygyro)
                                telemetria_actual["imu"]["gyro_z"] = limpiar_float(msg.zgyro)
                                telemetria_actual["imu"]["mag_x"] = limpiar_float(msg.xmag)
                                telemetria_actual["imu"]["mag_y"] = limpiar_float(msg.ymag)
                                telemetria_actual["imu"]["mag_z"] = limpiar_float(msg.zmag)
                                telemetria_actual["imu"]["presion_hpa"] = limpiar_float(msg.abs_pressure, 1013.2)
                                telemetria_actual["sistema"]["temperatura_placa"] = limpiar_float(msg.temperature, 25.0)

                        elif tipo == 'SERVO_OUTPUT_RAW':
                            telemetria_actual["actuadores"]["motor1_pwm"] = msg.servo1_raw
                            telemetria_actual["actuadores"]["motor2_pwm"] = msg.servo2_raw
                            telemetria_actual["actuadores"]["motor3_pwm"] = msg.servo3_raw
                            telemetria_actual["actuadores"]["motor4_pwm"] = msg.servo4_raw
                            if hasattr(msg, 'servo5_raw'):
                                telemetria_actual["actuadores"]["motor5_pwm"] = msg.servo5_raw
                                telemetria_actual["actuadores"]["motor6_pwm"] = msg.servo6_raw
                                telemetria_actual["actuadores"]["motor7_pwm"] = msg.servo7_raw
                                telemetria_actual["actuadores"]["motor8_pwm"] = msg.servo8_raw

                        elif tipo == 'RC_CHANNELS':
                            telemetria_actual["rc"]["ch1"] = msg.chan1_raw
                            telemetria_actual["rc"]["ch2"] = msg.chan2_raw
                            telemetria_actual["rc"]["ch3"] = msg.chan3_raw
                            telemetria_actual["rc"]["ch4"] = msg.chan4_raw
                            telemetria_actual["rc"]["ch5"] = msg.chan5_raw
                            telemetria_actual["rc"]["ch6"] = msg.chan6_raw
                            telemetria_actual["rc"]["ch7"] = msg.chan7_raw
                            telemetria_actual["rc"]["ch8"] = msg.chan8_raw
                            telemetria_actual["rc"]["rssi"] = msg.rssi

                        elif tipo == 'PARAM_VALUE':
                            param_id = msg.param_id
                            if isinstance(param_id, bytes):
                                param_id = param_id.decode('ascii', errors='ignore').rstrip('\x00')
                            telemetria_actual["parametros"][param_id] = round(msg.param_value, 4)

                        elif tipo == 'STATUSTEXT':
                            texto = msg.text
                            if isinstance(texto, bytes):
                                texto = texto.decode('utf-8', errors='ignore')
                            telemetria_actual["mensajes_estado"].append({
                                "tiempo": tiempo_actual,
                                "severidad": msg.severity,
                                "texto": texto
                            })
                            if len(telemetria_actual["mensajes_estado"]) > 150:
                                telemetria_actual["mensajes_estado"].pop(0)

                        if time.time() - ultimo_print_tiempo > 2.5:
                            ultimo_print_tiempo = time.time()
                            print(f"[MAVLink {hz if 'hz' in locals() else 0}Hz] T:{tiempo_actual}s | Pitch:{telemetria_actual['pitch']} | Roll:{telemetria_actual['roll']} | Modo:{telemetria_actual['sistema']['modo_vuelo']} | Arm:{telemetria_actual['sistema']['armado']}")

                    else:
                        if time.time() - ultimo_mensaje_tiempo > 3.5:
                            telemetria_actual["conectado"] = False
                            telemetria_actual["conexion"]["conectado"] = False
                            config_conexion["conectado"] = False

        except Exception as e:
            print(f"[Telemetría] Error de conexión: {e}. Reintentando en 3s...")
            with conexion_lock:
                conexion = None
            telemetria_actual["conectado"] = False
            config_conexion["conectado"] = False
            config_conexion["estado_texto"] = f"Error: {e}"
            time.sleep(3)


# --- HILO DE SIMULACIÓN Y REPRODUCCIÓN CSV ---
def simulador_csv_worker():
    global telemetria_actual, config_conexion
    
    filas_csv = []
    if os.path.exists(ARCHIVO_LOG_ACTUAL):
        try:
            with open(ARCHIVO_LOG_ACTUAL, mode='r', newline='') as f:
                reader = csv.DictReader(f)
                filas_csv = list(reader)
        except Exception as e:
            print(f"[Simulador] Error leyendo CSV: {e}")
            
    if not filas_csv:
        print("[Simulador] Generando datos dinámicos de prueba sintéticos.")
        for t in range(500):
            seg = t * 0.1
            filas_csv.append({
                "Tiempo(s)": str(round(seg, 2)),
                "Pitch(rad)": str(round(0.25 * math.sin(seg * 0.8), 3)),
                "Roll(rad)": str(round(0.35 * math.cos(seg * 0.5), 3)),
                "Yaw(rad)": str(round((seg * 0.1) % (math.pi * 2), 3)),
                "AltRel(m)": str(round(15.0 + 4.0 * math.sin(seg * 0.2), 2)),
                "Groundspeed(m/s)": str(round(5.0 + 2.0 * math.cos(seg * 0.3), 2)),
                "Voltaje(V)": str(round(15.8 - (seg * 0.005), 2)),
                "Corriente(A)": str(round(12.5 + 3.0 * math.sin(seg), 2)),
                "Bateria(%)": str(max(int(100 - (seg * 0.1)), 15)),
                "Latitud": str(round(-33.467225 + 0.00015 * math.cos(seg * 0.05), 7)),
                "Longitud": str(round(-70.657605 + 0.00018 * math.sin(seg * 0.05), 7)),
                "Satellites": "14",
                "ModoVuelo": "POSCTL",
                "VibeX": str(round(12.0 + 4.0 * math.sin(seg * 2), 1)),
                "VibeY": str(round(14.0 + 5.0 * math.cos(seg * 2), 1)),
                "VibeZ": str(round(18.0 + 3.0 * math.sin(seg * 3), 1))
            })

    telemetria_actual["simulador"]["total"] = len(filas_csv)
    idx = 0
    
    while hilo_receptor_activo:
        if config_conexion["modo_simulacion"]:
            try:
                row = filas_csv[idx]
                t_val = float(row.get("Tiempo(s)", idx * 0.1))
                pitch = float(row.get("Pitch(rad)", 0))
                roll = float(row.get("Roll(rad)", 0))
                yaw = float(row.get("Yaw(rad)", 0))
                alt_rel = float(row.get("AltRel(m)", 10))
                speed = float(row.get("Groundspeed(m/s)", 4))
                volt = float(row.get("Voltaje(V)", 15.5))
                curr = float(row.get("Corriente(A)", 10.0))
                bat_pct = int(float(row.get("Bateria(%)", 85)))
                lat = float(row.get("Latitud", -33.467225))
                lon = float(row.get("Longitud", -70.657605))
                sats = int(row.get("Satellites", 12))
                modo = row.get("ModoVuelo", "POSCTL")
                vibe_x = float(row.get("VibeX", 12.0))
                vibe_y = float(row.get("VibeY", 14.0))
                vibe_z = float(row.get("VibeZ", 18.0))

                telemetria_actual["conectado"] = True
                telemetria_actual["tiempo"] = t_val
                telemetria_actual["hz_recepcion"] = 20.0
                telemetria_actual["pitch"] = pitch
                telemetria_actual["roll"] = roll
                telemetria_actual["yaw"] = yaw
                
                telemetria_actual["actitud"]["pitch"] = pitch
                telemetria_actual["actitud"]["roll"] = roll
                telemetria_actual["actitud"]["yaw"] = yaw
                telemetria_actual["actitud"]["pitch_deg"] = round(math.degrees(pitch), 1)
                telemetria_actual["actitud"]["roll_deg"] = round(math.degrees(roll), 1)
                telemetria_actual["actitud"]["yaw_deg"] = round((math.degrees(yaw) + 360) % 360, 1)

                telemetria_actual["vfr_hud"]["groundspeed"] = speed
                telemetria_actual["vfr_hud"]["airspeed"] = speed * 1.05
                telemetria_actual["vfr_hud"]["altitud_baro"] = alt_rel
                telemetria_actual["vfr_hud"]["heading"] = int((math.degrees(yaw) + 360) % 360)
                telemetria_actual["vfr_hud"]["climb"] = round(0.5 * math.sin(t_val), 2)

                telemetria_actual["gps"]["lat"] = lat
                telemetria_actual["gps"]["lon"] = lon
                telemetria_actual["gps"]["alt_rel"] = alt_rel
                telemetria_actual["gps"]["alt_amsl"] = round(alt_rel + 560.0, 2)
                telemetria_actual["gps"]["satellites"] = sats
                telemetria_actual["gps"]["fix_desc"] = "3D Fix"
                telemetria_actual["gps"]["fix_type"] = 3
                telemetria_actual["gps"]["hdop"] = 0.8

                telemetria_actual["sistema"]["voltaje_bateria"] = volt
                telemetria_actual["sistema"]["corriente_bateria"] = curr
                telemetria_actual["sistema"]["bateria_pct"] = bat_pct
                telemetria_actual["sistema"]["voltaje_celda"] = round(volt / 4.0, 2)
                telemetria_actual["sistema"]["modo_vuelo"] = modo
                telemetria_actual["sistema"]["armado"] = True
                telemetria_actual["sistema"]["carga_cpu"] = 28.5

                telemetria_actual["vibracion"]["vibe_x"] = vibe_x
                telemetria_actual["vibracion"]["vibe_y"] = vibe_y
                telemetria_actual["vibracion"]["vibe_z"] = vibe_z
                telemetria_actual["vibracion"]["nivel_salud"] = "Excelente (<30 m/s²)"

                telemetria_actual["actuadores"]["motor1_pwm"] = int(1450 + 100 * math.sin(t_val))
                telemetria_actual["actuadores"]["motor2_pwm"] = int(1450 - 100 * math.sin(t_val))
                telemetria_actual["actuadores"]["motor3_pwm"] = int(1450 + 100 * math.cos(t_val))
                telemetria_actual["actuadores"]["motor4_pwm"] = int(1450 - 100 * math.cos(t_val))

                telemetria_actual["simulador"]["activo"] = True
                telemetria_actual["simulador"]["indice"] = idx
                telemetria_actual["conexion"]["simulacion"] = True
                telemetria_actual["conexion"]["conectado"] = True
                telemetria_actual["conexion"]["estado"] = "Simulación CSV en Vivo"

                idx = (idx + 1) % len(filas_csv)
                delay = 0.05 / max(telemetria_actual["simulador"]["velocidad"], 0.1)
                time.sleep(delay)
            except Exception as ex:
                print(f"[Simulador Error] {ex}")
                time.sleep(0.5)
        else:
            time.sleep(0.2)


# --- RUTAS WEB Y API REST ---
@app.route('/')
def home():
    return render_template('index.html')

@app.route('/api/datos')
def obtener_datos():
    return jsonify(telemetria_actual)

@app.route('/api/conexiones/puertos')
def api_listar_puertos():
    puertos = listar_puertos()
    return jsonify({
        "status": "ok",
        "puertos": puertos,
        "conexion_actual": config_conexion
    })

@app.route('/api/conectar', methods=['POST'])
def api_conectar():
    global conexion, config_conexion
    data = request.get_json(silent=True) or request.form
    puerto = data.get("puerto", PUERTO_DEFECTO)
    baud = int(data.get("baud", BAUD_DEFECTO))
    
    with conexion_lock:
        if conexion is not None:
            try:
                conexion.close()
            except Exception:
                pass
            conexion = None
            
    config_conexion["puerto"] = puerto
    config_conexion["baud"] = baud
    config_conexion["deseado_conectar"] = True
    config_conexion["modo_simulacion"] = False
    telemetria_actual["simulador"]["activo"] = False
    
    return jsonify({
        "status": "ok",
        "mensaje": f"Conectando a {puerto} a {baud} baudios...",
        "puerto": puerto,
        "baud": baud
    })

@app.route('/api/desconectar', methods=['POST'])
def api_desconectar():
    global conexion, config_conexion
    with conexion_lock:
        if conexion is not None:
            try:
                conexion.close()
            except Exception:
                pass
            conexion = None
    config_conexion["conectado"] = False
    config_conexion["deseado_conectar"] = False
    config_conexion["estado_texto"] = "Desconectado"
    telemetria_actual["conectado"] = False
    telemetria_actual["conexion"]["conectado"] = False
    
    return jsonify({"status": "ok", "mensaje": "Desconectado exitosamente del Pixhawk."})

@app.route('/api/simulacion/<accion>', methods=['POST'])
def api_control_simulacion(accion):
    global config_conexion, telemetria_actual
    if accion == "iniciar":
        config_conexion["modo_simulacion"] = True
        telemetria_actual["simulador"]["activo"] = True
        return jsonify({"status": "ok", "mensaje": "Simulador de vuelo CSV iniciado."})
    elif accion == "detener":
        config_conexion["modo_simulacion"] = False
        telemetria_actual["simulador"]["activo"] = False
        telemetria_actual["conectado"] = False
        return jsonify({"status": "ok", "mensaje": "Simulador detenido."})
    elif accion == "velocidad":
        vel = float(request.args.get("vel", 1.0))
        telemetria_actual["simulador"]["velocidad"] = vel
        return jsonify({"status": "ok", "velocidad": vel})
    return jsonify({"status": "error", "mensaje": "Acción desconocida"}), 400

@app.route('/api/modo/<nombre_modo>', methods=['POST'])
def api_cambiar_modo(nombre_modo):
    exito, msg = cambiar_modo_vuelo_cmd(nombre_modo)
    return jsonify({"status": "ok" if exito else "error", "mensaje": msg})

@app.route('/api/armar/<int:estado>', methods=['POST'])
def api_armar_dron(estado):
    armar = (estado == 1)
    force = request.args.get("force", "0") == "1"
    exito, msg = armar_desarmar_cmd(armar, force)
    return jsonify({"status": "ok" if exito else "error", "mensaje": msg})

@app.route('/api/motor/<int:motor_id>/<valor>', methods=['POST', 'GET'])
def controlar_motor(motor_id, valor):
    try:
        valor_flotante = float(valor)
    except ValueError:
        return jsonify({ "status": "error", "mensaje": "Valor numérico requerido" }), 400

    timeout = float(request.args.get("timeout", 3.0))
    exito, mensaje = enviar_comando_motor(motor_id, valor_flotante, timeout)
    return jsonify({
        "status": "ok" if exito else "error",
        "motor": motor_id,
        "valor": valor_flotante,
        "mensaje": mensaje
    })

@app.route('/api/motor/stop_all', methods=['POST', 'GET'])
def detener_todos_los_motores():
    mensajes = []
    for m_id in range(1, 9):
        exito, msg = enviar_comando_motor(m_id, 0)
        if exito:
            mensajes.append(msg)
            
    return jsonify({
        "status": "ok",
        "mensaje": "Todos los motores han sido detenidos de forma segura."
    })

@app.route('/api/parametro/<nombre>', methods=['GET'])
def api_obtener_parametro(nombre):
    if nombre in telemetria_actual["parametros"]:
        return jsonify({"status": "ok", "parametro": nombre, "valor": telemetria_actual["parametros"][nombre]})
    exito, msg = leer_parametro_mavlink(nombre)
    return jsonify({"status": "ok" if exito else "error", "mensaje": msg})

@app.route('/api/parametro/<nombre>/<valor>', methods=['POST'])
def api_escribir_parametro(nombre, valor):
    exito, msg = escribir_parametro_mavlink(nombre, valor)
    return jsonify({"status": "ok" if exito else "error", "mensaje": msg})

@app.route('/api/descargar_log')
def descargar_log():
    try:
        if os.path.exists(ARCHIVO_LOG_ACTUAL):
            return send_file(ARCHIVO_LOG_ACTUAL, as_attachment=True, download_name="telemetria_pixhawk_log.csv")
        return jsonify({"status": "error", "mensaje": "No hay log de telemetría registrado."}), 404
    except Exception as e:
        return jsonify({"status": "error", "mensaje": str(e)}), 404

# --- SERVER-SENT EVENTS (SSE STREAMING ULTRA-RÁPIDO) ---
@app.route('/api/stream')
def sse_telemetria():
    def generar():
        while True:
            datos_json = json.dumps(telemetria_actual)
            yield f"data: {datos_json}\n\n"
            time.sleep(0.05) # 20 Hz
    return Response(generar(), mimetype='text/event-stream')


# --- INICIALIZACIÓN ---
if __name__ == '__main__':
    hilo_telemetria = threading.Thread(target=receptor_mavlink_worker, daemon=True)
    hilo_telemetria.start()
    
    hilo_sim = threading.Thread(target=simulador_csv_worker, daemon=True)
    hilo_sim.start()
    
    print("================================================================")
    print("🚀 GCS PIXHAWK 6X - ESTACIÓN TERRENA DE CONTROL AEROESPACIAL")
    print("🌐 Servidor listo en: http://localhost:5000")
    print("📡 Streaming SSE y API REST activos a 20Hz.")
    print("================================================================")
    
    app.run(host='0.0.0.0', port=5000, threaded=True)
