@echo off
chcp 65001 > nul
echo ========================================================
echo  🚀 Marino Editor - Despliegue a GitHub
echo ========================================================
echo.

set /p REPO_URL="Pega la URL de tu repositorio de GitHub (ej. https://github.com/erickrosas/marino-editor.git): "

if "%REPO_URL%"=="" (
    echo [ERROR] Debes proporcionar la URL del repositorio.
    pause
    exit /b 1
)

echo.
echo Vinculando repositorio remoto origin...
git remote remove origin 2>nul
git remote add origin %REPO_URL%

echo.
echo Subiendo la rama main a GitHub...
git branch -M main
git push -u origin main

echo.
if %ERRORLEVEL% equ 0 (
    echo ========================================================
    echo  ✅ Proyecto subido exitosamente a GitHub!
    echo ========================================================
) else (
    echo [ERROR] Fallo al subir. Verifica tus permisos o URL.
)

echo.
pause
