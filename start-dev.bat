@echo off
chcp 65001 >nul
title MRP II 系统开发环境

echo ========================================
echo    MRP II 系统 - 开发环境启动
echo ========================================
echo.
echo 请选择操作：
echo  1 - 启动 MySQL
echo  2 - 启动后端 (uvicorn)
echo  3 - 启动前端 (npm dev)
echo  4 - 启动 VS Code
echo  5 - 全部启动
echo.

set /p choice="请输入数字 (1-5): "

if "%choice%"=="1" goto start_mysql
if "%choice%"=="2" goto start_backend
if "%choice%"=="3" goto start_frontend
if "%choice%"=="4" goto start_vscode
if "%choice%"=="5" goto start_all
goto end

:start_mysql
echo.
echo 启动 MySQL...
start "MySQL" "D:\MySQL_Server_8.4\bin\mysqld" --defaults-file="D:\MDR II\mysql-config\my.ini" --standalone --console
echo MySQL 已启动
goto end

:start_backend
echo.
echo 启动后端 (localhost:8000)...
cd /d "D:\MDR II\backend"
start "Backend" cmd /k "D:\Python311\python.exe -m uvicorn app.main:app --reload --host 0.0.0.0 --port 8000"
echo 后端已启动: http://localhost:8000
echo API 文档: http://localhost:8000/docs
goto end

:start_frontend
echo.
echo 启动前端 (localhost:5173)...
cd /d "D:\MDR II\frontend"
start "Frontend" cmd /k "D:\NodeJS\npm.cmd run dev"
echo 前端已启动: http://localhost:5173
goto end

:start_vscode
echo.
echo 启动 VS Code...
start "" "D:\VSCode\Code.exe" "D:\MDR II"
goto end

:start_all
echo.
echo 1/4 启动 MySQL...
start "MySQL" "D:\MySQL_Server_8.4\bin\mysqld" --defaults-file="D:\MDR II\mysql-config\my.ini" --standalone --console
timeout /t 3 /nobreak >nul

echo 2/4 启动后端...
cd /d "D:\MDR II\backend"
start "Backend" cmd /k "D:\Python311\python.exe -m uvicorn app.main:app --reload --host 0.0.0.0 --port 8000"

echo 3/4 启动前端...
cd /d "D:\MDR II\frontend"
start "Frontend" cmd /k "D:\NodeJS\npm.cmd run dev"

echo 4/4 打开 VS Code...
start "" "D:\VSCode\Code.exe" "D:\MDR II"

echo.
echo ✅ 全部启动完成！
echo    后端: http://localhost:8000
echo    API:  http://localhost:8000/docs
echo    前端: http://localhost:5173
echo.
goto end

:end
pause
