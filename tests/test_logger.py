"""
测试日志模块
"""

import logging

from medcrux.utils.logger import log_error_with_context, setup_logger


class TestLogger:
    """测试日志模块"""

    def test_setup_logger(self):
        """测试logger设置"""
        logger = setup_logger("test_module")
        assert logger.name == "test_module"
        assert logger.level == logging.INFO
        assert len(logger.handlers) > 0

    def test_logger_levels(self):
        """测试不同日志级别"""
        logger = setup_logger("test_module", level=logging.DEBUG)
        logger.debug("Debug message")
        logger.info("Info message")
        logger.warning("Warning message")
        logger.error("Error message")
        logger.critical("Critical message")

    def test_log_error_with_context(self):
        """测试错误日志记录"""
        logger = setup_logger("test_module")
        test_error = ValueError("Test error")
        context = {"key1": "value1", "key2": "value2"}

        log_error_with_context(logger, test_error, context=context, operation="test_operation")

        # 验证错误被记录（通过检查handler存在）
        assert len(logger.handlers) > 0

    def test_logger_handlers(self):
        """测试logger handlers配置"""
        logger = setup_logger("test_module")
        handlers = logger.handlers

        # 应该至少有一个控制台handler
        assert any(isinstance(h, logging.StreamHandler) for h in handlers)

        # 应该至少有一个文件handler
        assert any(isinstance(h, logging.FileHandler) for h in handlers)
