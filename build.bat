REM filepath: d:\Billing\BillingApp\build.bat
@echo off
echo Building Billing System...

REM Create required directories if they don't exist
if not exist "database" mkdir database
if not exist "bills" mkdir bills
if not exist "logs" mkdir logs
if not exist "Output" mkdir Output

REM Build Python executable
echo Building Python executable...
python setup.py

REM Compile Inno Setup installer
echo Creating installer...
"C:\Program Files (x86)\Inno Setup 6\ISCC.exe" setup.iss

echo Build complete! Check Output folder for installer.
pause