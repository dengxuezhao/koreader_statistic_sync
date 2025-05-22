@echo off
REM KOmpanion 启动脚本 (Windows)

echo 正在启动 KOmpanion 应用程序...

REM 检查是否有额外参数
set "args="
:parse_args
if "%~1"=="" goto :run
set "args=%args% %~1"
shift
goto :parse_args

:run
if "%args%"=="" (
    echo 使用默认设置启动 (127.0.0.1:8080)
    python run.py
) else (
    echo 使用自定义设置启动: %args%
    python run.py%args%
)

if %ERRORLEVEL% NEQ 0 (
    echo.
    echo 启动失败！错误代码：%ERRORLEVEL%
    echo.
    echo 常见问题:
    echo - 确保您已安装所有依赖 (pip install -r requirements.txt)
    echo - 确保端口未被占用
    echo - 检查 .env 文件是否存在并配置正确
    echo.
    pause
) 