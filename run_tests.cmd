@echo off
setlocal
cd /d "%~dp0.."
call activate
cd /d "%~dp0"
python -u "%~dp0..\runtime\tools\cl\runtime\run_tests.py" runtime
set "EXIT_CODE=%ERRORLEVEL%"
endlocal & exit /b %EXIT_CODE%
