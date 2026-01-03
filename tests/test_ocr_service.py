"""
测试OCR服务模块
"""

from unittest.mock import patch

import numpy as np
import pytest

from medcrux.ingestion.ocr_service import extract_text_from_bytes


class TestOCRService:
    """测试OCR服务"""

    def test_extract_text_from_bytes_invalid_image(self):
        """测试无效图片"""
        invalid_bytes = b"not an image"
        with pytest.raises(ValueError):
            extract_text_from_bytes(invalid_bytes)

    def test_extract_text_from_bytes_empty_bytes(self):
        """测试空字节流"""
        empty_bytes = b""
        with pytest.raises(ValueError):
            extract_text_from_bytes(empty_bytes)

    @patch("medcrux.ingestion.ocr_service.engine")
    @patch("cv2.imdecode")
    def test_extract_text_from_bytes_success(self, mock_imdecode, mock_engine):
        """测试成功提取文本"""
        # Mock图像解码
        mock_image = np.zeros((100, 100, 3), dtype=np.uint8)
        mock_imdecode.return_value = mock_image

        # Mock OCR结果
        mock_engine.return_value = (
            [
                [[0, 0, 10, 10], "超声描述", 0.95],
                [[10, 10, 20, 20], "左乳上方", 0.92],
            ],
            None,
        )

        # 创建有效的图片字节流（模拟）
        image_bytes = b"\x89PNG\r\n\x1a\n" + b"0" * 100

        result = extract_text_from_bytes(image_bytes)

        assert isinstance(result, str)
        assert "超声描述" in result
        assert "左乳上方" in result
        assert mock_engine.called

    @patch("medcrux.ingestion.ocr_service.engine")
    @patch("cv2.imdecode")
    def test_extract_text_from_bytes_empty_result(self, mock_imdecode, mock_engine):
        """测试OCR结果为空"""
        # Mock图像解码
        mock_image = np.zeros((100, 100, 3), dtype=np.uint8)
        mock_imdecode.return_value = mock_image

        # Mock OCR结果为空
        mock_engine.return_value = ([], None)

        image_bytes = b"\x89PNG\r\n\x1a\n" + b"0" * 100

        result = extract_text_from_bytes(image_bytes)

        assert result == ""

    @patch("cv2.imdecode")
    def test_extract_text_from_bytes_decode_failure(self, mock_imdecode):
        """测试图像解码失败"""
        # Mock图像解码返回None
        mock_imdecode.return_value = None

        image_bytes = b"invalid image data"

        with pytest.raises(ValueError):
            extract_text_from_bytes(image_bytes)
