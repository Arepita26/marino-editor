@echo off
chcp 65001 > nul
echo ========================================================
echo  🚀 Marino Editor - Despliegue a Hugging Face Spaces
echo ========================================================
echo.

set SPACE_NAME=marino-editor-api
set /p HF_USER="Introduce tu usuario de Hugging Face (ej. erickrosas): "

if "%HF_USER%"=="" (
    echo [ERROR] Debes introducir un usuario valido de Hugging Face.
    pause
    exit /b 1
)

echo.
echo Conectando con https://huggingface.co/spaces/%HF_USER%/%SPACE_NAME% ...
git remote remove space 2>nul
git remote add space https://huggingface.co/spaces/%HF_USER%/%SPACE_NAME%

echo.
echo Subiendo la carpeta backend y el intro oficial permanente...
git subtree push --prefix backend space main

echo.
if %ERRORLEVEL% equ 0 (
    echo ========================================================
    echo  ✅ Backend subido exitosamente a Hugging Face!
    echo  Tu API estara lista en:
    echo  https://%HF_USER%-%SPACE_NAME%.hf.space/api/health
    echo ========================================================
) else (
    echo.
    echo [AVISO] Si es la primera vez que subes, asegurate de haber creado
    echo el Space en https://huggingface.co/new-space con SDK Docker (Blank).
)

echo.
pause
