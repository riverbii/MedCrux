"""
OCR服务模块：从图片中提取文本

根据STANDARDS_v1.1.md要求：
- 基础日志记录：记录关键操作和错误
- 错误追踪：所有异常必须被捕获并记录
"""

import cv2
import numpy as np
from rapidocr_onnxruntime import RapidOCR

from medcrux.utils.logger import log_error_with_context, setup_logger

# 初始化logger
logger = setup_logger("medcrux.ingestion")

# 初始化 OCR 引擎
# det_use_gpu=False, cls_use_gpu=False, rec_use_gpu=False
# 强制使用 CPU 运行，确保在任何普通电脑上都能跑，不会因为没显卡报错
engine = RapidOCR(det_use_gpu=False, cls_use_gpu=False, rec_use_gpu=False)
logger.info("OCR引擎初始化完成")


def extract_text_from_bytes(image_bytes: bytes) -> str:
    """
    接收图片字节流，返回识别出的纯文本。

    Args:
        image_bytes: 图片字节流

    Returns:
        识别出的文本字符串

    Raises:
        ValueError: 图片格式无效或无法解析
        Exception: OCR处理过程中的其他错误
    """
    context = {"image_size": len(image_bytes)}
    logger.debug(f"开始OCR识别 [图片大小: {len(image_bytes)} bytes]")

    # 检查空字节流
    if not image_bytes or len(image_bytes) == 0:
        error_msg = "图片字节流为空"
        logger.error(error_msg)
        raise ValueError(error_msg)

    try:
        # 1. 将字节流转换为 numpy 数组 (这是 OpenCV 能看懂的格式)
        nparr = np.frombuffer(image_bytes, np.uint8)

        # 2. 解码为图像
        img = cv2.imdecode(nparr, cv2.IMREAD_COLOR)

        if img is None:
            error_msg = "无法解析图像文件，可能格式不支持或文件损坏"
            logger.error(error_msg)
            raise ValueError(error_msg)

        logger.debug(f"图像解码成功 [尺寸: {img.shape}]")

        # 3. 运行 OCR
        # result 结构: [[box, text, score], ...]
        result, _ = engine(img)

        if not result:
            logger.warning("OCR识别结果为空")
            return ""

        # 4. 提取纯文本
        # 我们把所有识别出来的碎片文字拼成一个长字符串，用换行符分隔
        all_text = [line[1] for line in result]
        text = "\n".join(all_text)

        logger.info(f"OCR识别完成 [识别行数: {len(all_text)}, 文本长度: {len(text)}]")
        return text

    except ValueError:
        # ValueError直接抛出
        raise
    except Exception as e:
        # 捕获所有其他异常
        log_error_with_context(logger, e, context=context, operation="OCR识别")
        raise


if __name__ == "__main__":
    # 简单的测试代码 (你可以自己放一张图在根目录测试)
    print("OCR Service Loaded. Ready to read.")
