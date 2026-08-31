@echo off
title Estacion Terrena Holybro X650 (Pixhawk 6X) - UBO
echo ====================================================================
echo   INICIANDO ESTACION TERRENA GCS - HOLYBRO X650 / PIXHAWK 6X
echo   Universidad Bernardo O'Higgins (UBO)
echo ====================================================================
echo.

echo [1/2] Verificando dependencias...
python -m pip install -r requirements.txt --quiet

echo [2/2] Iniciando Servidor GCS (Flask + MAVLink 20Hz)...
start http://localhost:5000
python app.py

pause
