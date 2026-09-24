@echo off
rem Doppelklick startet bskitool (Windows). Fenster offen lassen.
cd /d "%~dp0"
where python >nul 2>nul || (echo Python fehlt - bitte von python.org installieren ^(Haken bei "Add to PATH"^). & pause & exit /b 1)
python bskitool.py ui
pause
