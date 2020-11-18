@echo off
python --version 3>NUL
if errorlevel 1 goto errorNoPython
python MoticDownloader.py
goto:eof
:errorNoPython
echo.
echo Error^: Python not installed. Please install from https://www.python.org/downloads
