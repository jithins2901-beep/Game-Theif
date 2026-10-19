# run_game.ps1 — launch the game without manually activating the venv
# Usage: right-click → "Run with PowerShell"  OR  just run: .\run_game.ps1

Set-ExecutionPolicy -Scope Process -ExecutionPolicy Bypass
$scriptDir = Split-Path -Parent $MyInvocation.MyCommand.Path
Set-Location $scriptDir
& "$scriptDir\.venv\Scripts\python.exe" main.py
