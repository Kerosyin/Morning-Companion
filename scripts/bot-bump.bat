@echo off
if "%~1"=="" (
  set LVL=patch
) else (
  set LVL=%~1
)
powershell -NoProfile -ExecutionPolicy Bypass -File "%~dp0bot.ps1" bump "%LVL%"
pause