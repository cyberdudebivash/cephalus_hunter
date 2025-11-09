@echo off
echo Installing Cephalus Hunter Dependencies...
pip install -r requirements.txt
echo.
echo Installing pywin32 (RDP support)...
python -m pip install pywin32
echo.
echo Setup Complete! Run: python gui.py
pause