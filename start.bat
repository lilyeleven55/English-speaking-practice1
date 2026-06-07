@echo off
echo ========================================
echo    AI 英语口语陪练 - 启动脚本
echo ========================================
echo.
echo 正在启动应用...
echo 访问地址: http://127.0.0.1:5000
echo.
echo 按 Ctrl+C 可以停止服务器
echo.
echo ========================================
echo.

python app.py

if errorlevel 1 (
    echo.
    echo [错误] 启动失败！
    echo 请确保已安装依赖: pip install -r requirements.txt
    echo 并确保已配置 .env 文件中的 ZHIPU_API_KEY
    pause
)
