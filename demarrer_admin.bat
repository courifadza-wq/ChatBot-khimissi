@echo off
title Admin Bot WhatsApp - Interface
color 0B
cd /d "%~dp0"
echo.
echo   ======================================================
echo       ADMIN BOT WHATSAPP - Interface d'alimentation
echo   ======================================================
echo.

REM ---------- Detection de Python (py puis python) ----------
set "PYCMD="
where py >nul 2>nul
if not errorlevel 1 ( set "PYCMD=py" & goto found )
where python >nul 2>nul
if not errorlevel 1 ( set "PYCMD=python" & goto found )

echo   [ERREUR] Python non detecte.
echo   Installe-le sur https://www.python.org/downloads/
echo   IMPORTANT : coche "Add Python to PATH".
pause
exit /b

:found
echo   [OK] Python detecte : %PYCMD%

REM ---------- Lancement du serveur (aucune installation requise) ----------
echo   Lancement du serveur sur http://localhost:8080 ...
start "AdminBotServer" cmd /k "%PYCMD% admin_server.py"

REM ---------- Attente + ouverture navigateur ----------
timeout /t 4 /nobreak >nul
start "" "http://localhost:8080"

echo.
echo   Interface ouverte dans le navigateur.
echo   Garde la fenetre "AdminBotServer" OUVERTE (c'est le serveur).
echo   Pour arreter : ferme cette fenetre.
echo.
pause
