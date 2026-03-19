@echo off
title OpenEMR CDS Server
cd /d "%~dp0"
echo.
echo ========================================
echo  OpenEMR Clinical Decision Support Server
echo ========================================
echo.
echo Starting server on port 3005...
echo API docs: http://localhost:3005
echo.
echo Press Ctrl+C to stop
echo.
python openemr_cds_server.py
pause
