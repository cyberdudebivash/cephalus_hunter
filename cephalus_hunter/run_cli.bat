@echo off
echo Cephalus Hunter CLI Test
python cli.py --scan --export json
echo.
python cli.py --scan --export csv
pause