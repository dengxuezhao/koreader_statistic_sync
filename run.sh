#!/bin/bash
# KOmpanion 启动脚本 (Linux/macOS)

echo "正在启动 KOmpanion 应用程序..."

# 给予脚本执行权限
chmod +x run.py

# 启动应用程序
python run.py "$@"

EXIT_CODE=$?

if [ $EXIT_CODE -ne 0 ]; then
  echo ""
  echo "启动失败！错误代码：$EXIT_CODE"
  echo ""
  echo "常见问题:"
  echo "- 确保您已安装所有依赖 (pip install -r requirements.txt)"
  echo "- 确保端口未被占用"
  echo "- 检查 .env 文件是否存在并配置正确"
  echo ""
  read -p "按回车键继续..." key
fi 