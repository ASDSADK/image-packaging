@echo off
REM === CASS 10.1 for AutoCAD 2023 启动脚本 ===
REM 解决 ARX 找不到依赖 DLL 的问题

set CASS_ROOT=D:\CASS\CASS11 For AutoCAD 2023

REM 将 CASS 的所有 DLL 目录加入 PATH（仅本次启动有效）
set PATH=%CASS_ROOT%\bin;%CASS_ROOT%\bin\plugins;%CASS_ROOT%\bin\qtplugins;%CASS_ROOT%\bin\qtplugins\platforms;%CASS_ROOT%\bin_lsp;%CASS_ROOT%\bin\smarttabletool;%CASS_ROOT%\bin\smarttabletool\lua;%CASS_ROOT%\bin\lua;%CASS_ROOT%\bin\socket;%CASS_ROOT%\bin\luasql;%PATH%

REM 启动 AutoCAD 2023 并加载 CASS
start "CASS 10.1" "D:\CAD2023\AutoCAD 2023\acad.exe" /p Cass10.1 /b "%CASS_ROOT%\system\cass_startup.scr" /nologo
