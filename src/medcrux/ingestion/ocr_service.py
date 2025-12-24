import cv2
import numpy as np
from rapidocr_onnxruntime import RapidOCR

# 初始化 OCR 引擎
# det_use_gpu=False, cls_use_gpu=False, rec_use_gpu=False
# 强制使用 CPU 运行，确保在任何普通电脑上都能跑，不会因为没显卡报错
engine = RapidOCR(det_use_gpu=False, cls_use_gpu=False, rec_use_gpu=False)


def extract_text_from_bytes(image_bytes: bytes) -> str:
    """
    接收图片字节流，返回识别出的纯文本。
    """
    # 1. 将字节流转换为 numpy 数组 (这是 OpenCV 能看懂的格式)
    nparr = np.frombuffer(image_bytes, np.uint8)

    # 2. 解码为图像
    img = cv2.imdecode(nparr, cv2.IMREAD_COLOR)

    if img is None:
        return "Error: 无法解析图像文件"

    # 3. 运行 OCR
    # result 结构: [[box, text, score], ...]
    result, _ = engine(img)

    if not result:
        return ""

    # 4. 提取纯文本
    # 我们把所有识别出来的碎片文字拼成一个长字符串，用换行符分隔
    all_text = [line[1] for line in result]

    return "\n".join(all_text)


if __name__ == "__main__":
    # 简单的测试代码 (你可以自己放一张图在根目录测试)
    print("OCR Service Loaded. Ready to read.")
