#!/usr/bin/env python
"""
KOmpanion 启动脚本
用于简化应用程序的启动过程
"""

import os
import sys
import argparse
import uvicorn
import logging

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    handlers=[
        logging.StreamHandler(sys.stdout)
    ]
)

logger = logging.getLogger("kompanion")

def parse_args():
    """解析命令行参数"""
    parser = argparse.ArgumentParser(description="KOmpanion 应用程序启动脚本")
    parser.add_argument(
        "--host", 
        type=str, 
        default="127.0.0.1", 
        help="主机地址 (默认: 127.0.0.1)"
    )
    parser.add_argument(
        "--port", 
        type=int, 
        default=8080, 
        help="端口号 (默认: 8080)"
    )
    parser.add_argument(
        "--reload", 
        action="store_true", 
        help="启用热重载模式 (开发环境适用)"
    )
    parser.add_argument(
        "--no-log", 
        action="store_true", 
        help="禁用日志输出"
    )
    return parser.parse_args()

def main():
    """主函数"""
    args = parse_args()
    
    if args.no_log:
        import logging
        logging.getLogger("uvicorn").setLevel(logging.WARNING)
        logging.getLogger("uvicorn.access").setLevel(logging.WARNING)
    
    logger.info(f"启动 KOmpanion 应用程序于 {args.host}:{args.port}")
    
    # 检查环境变量
    if not os.path.exists(".env"):
        logger.warning("没有找到 .env 文件，将使用默认配置")
    
    # 启动服务器
    uvicorn.run(
        "app.main:app",
        host=args.host,
        port=args.port,
        reload=args.reload,
        log_level="info" if not args.no_log else "warning"
    )

if __name__ == "__main__":
    main() 