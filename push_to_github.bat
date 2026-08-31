@echo off
title Subir Cambios a GitHub - Telemetria Holybro X650
color 0B
echo ====================================================================
echo   SUBIENDO PROYECTO A GITHUB: Telemetria_Holybro_x650
echo   Universidad Bernardo O'Higgins (UBO)
echo ====================================================================
echo.
echo Ejecutando: git push -u origin main
echo.

"C:\Program Files\Git\cmd\git.exe" push -u origin main

if %ERRORLEVEL% EQU 0 (
    echo.
    echo ====================================================================
    echo   [EXITO] Proyecto subido correctamente a GitHub!
    echo   https://github.com/Javiermoralesubo/Telemetria_Holybro_x650
    echo ====================================================================
) else (
    echo.
    echo ====================================================================
    echo   [NOTA] Si fallo la autenticacion, por favor verifica tus credenciales
    echo   de GitHub e intentalo nuevamente.
    echo ====================================================================
)

echo.
pause
