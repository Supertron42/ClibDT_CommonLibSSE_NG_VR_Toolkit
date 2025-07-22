@echo off
cd /d %~dp0

pyinstaller ClibDT.spec

pause