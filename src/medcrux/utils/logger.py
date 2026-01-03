"""
日志模块：提供基础日志记录和错误追踪功能

根据STANDARDS_v1.1.md要求：
- 基础日志记录：记录关键操作和错误
- 日志级别：DEBUG、INFO、WARNING、ERROR、CRITICAL
- 日志格式：结构化日志，包含时间戳、级别、模块、消息
- 异常捕获：所有异常必须被捕获并记录
- 错误记录：记录错误详情、堆栈信息、上下文信息
"""

import logging
import sys
from datetime import datetime
from pathlib import Path

# 配置日志格式
LOG_FORMAT = "%(asctime)s | %(levelname)-8s | %(name)s | %(message)s"
DATE_FORMAT = "%Y-%m-%d %H:%M:%S"

# 确保日志目录存在
LOG_DIR = Path("logs")
LOG_DIR.mkdir(exist_ok=True)

# 日志文件路径
LOG_FILE = LOG_DIR / f"medcrux_{datetime.now().strftime('%Y%m%d')}.log"
ERROR_LOG_FILE = LOG_DIR / f"medcrux_error_{datetime.now().strftime('%Y%m%d')}.log"


def setup_logger(name: str = "medcrux", level: int = logging.INFO) -> logging.Logger:
    """
    设置并返回配置好的logger

    Args:
        name: logger名称，通常是模块名
        level: 日志级别，默认INFO

    Returns:
        配置好的logger实例
    """
    logger = logging.getLogger(name)
    logger.setLevel(level)

    # 避免重复添加handler
    if logger.handlers:
        return logger

    # 控制台handler（输出到stdout）
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setLevel(level)
    console_formatter = logging.Formatter(LOG_FORMAT, DATE_FORMAT)
    console_handler.setFormatter(console_formatter)
    logger.addHandler(console_handler)

    # 文件handler（所有日志）
    file_handler = logging.FileHandler(LOG_FILE, encoding="utf-8")
    file_handler.setLevel(logging.DEBUG)  # 文件记录所有级别
    file_formatter = logging.Formatter(LOG_FORMAT, DATE_FORMAT)
    file_handler.setFormatter(file_formatter)
    logger.addHandler(file_handler)

    # 错误日志文件handler（只记录ERROR和CRITICAL）
    error_handler = logging.FileHandler(ERROR_LOG_FILE, encoding="utf-8")
    error_handler.setLevel(logging.ERROR)
    error_handler.setFormatter(file_formatter)
    logger.addHandler(error_handler)

    return logger


def log_error_with_context(
    logger: logging.Logger,
    error: Exception,
    context: dict | None = None,
    operation: str | None = None,
):
    """
    记录错误及其上下文信息

    Args:
        logger: logger实例
        error: 异常对象
        context: 上下文信息字典（如请求参数、用户信息等）
        operation: 操作名称（如"OCR识别"、"AI分析"等）
    """
    error_msg = "错误发生"
    if operation:
        error_msg += f" [操作: {operation}]"

    if context:
        context_str = ", ".join([f"{k}={v}" for k, v in context.items()])
        error_msg += f" [上下文: {context_str}]"

    logger.error(f"{error_msg}: {type(error).__name__}: {str(error)}", exc_info=True)


# 创建默认logger
default_logger = setup_logger("medcrux")
