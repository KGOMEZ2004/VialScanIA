@echo off
REM Inicia el servidor del Detector de Baches (doble clic o: .\iniciar_servidor.bat)
cd /d "%~dp0backend"
if exist ".venv\Scripts\activate.bat" call ".venv\Scripts\activate.bat"
echo.
echo  Detector de Baches Ecuador
echo  Pagina web: http://127.0.0.1:8000
echo  Para detener: Ctrl + C
echo.
start "" http://127.0.0.1:8000
python -m uvicorn app:app --host 0.0.0.0 --port 8000
pause
