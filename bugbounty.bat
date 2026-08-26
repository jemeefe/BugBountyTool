@echo off
REM BugBountyTool - Windows launcher
REM Uso: bugbounty.bat dominio.com

cd /d "%~dp0src"
python main.py %*
pause
