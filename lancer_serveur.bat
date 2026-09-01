@echo off
title Serveur Admin Bot WhatsApp
cd /d "%~dp0"

REM Lance le serveur et ENREGISTRE toute sa sortie dans server_log.txt
call ".venv\Scripts\activate.bat"
".venv\Scripts\python.exe" -m uvicorn app.admin_app:app --host 0.0.0.0 --port 8080 > "%~dp0server_log.txt" 2>&1

echo.
echo   ############################################################
echo   Le serveur s'est ARRETE.
echo   Si c'est une erreur, le detail est dans le fichier
echo   server_log.txt (a cote de ce script).
echo   Tu peux fermer cette fenetre.
echo   ############################################################
pause
