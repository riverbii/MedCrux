"""
BL-009 接口契约校验测试

测试目标：
1. 验证后端返回的数据结构是否符合接口契约
2. 验证字段映射是否正确（llm_birads_class → birads_class）
3. 验证位置信息标准化是否正确（quadrant → clock_position）

基于：docs/gov/FRONTEND_BACKEND_REVIEW_PROCESS.md
"""

import re
from unittest.mock import patch

import pytest
from fastapi.testclient import TestClient

from medcrux.api.main import app, _convert_quadrant_to_clock_position

client = TestClient(app)


class TestBL009APIContract:
    """BL-009接口契约校验测试类"""

    def test_backend_returns_birads_class_field(self):
        """
        测试后端返回的数据包含birads_class字段（前端期望的字段）
        
        验证：后端标准化逻辑是否正确映射llm_birads_class到birads_class
        """
        # 模拟analyze_birads_independently返回的数据
        mock_llm_independent_analysis = {
            "nodules": [
                {
                    "id": "nodule_1",
                    "llm_birads_class": "3",
                    "location": {
                        "breast": "left",
                        "clock_position": "11点",
                        "distance_from_nipple": "2.0",
                    },
                    "morphology": {
                        "shape": "椭圆形",
                        "boundary": "清晰",
                        "echo": "均匀低回声",
                        "orientation": "平行",
                    },
                }
            ],
            "llm_highest_birads": "3",
        }

        with patch("medcrux.api.main.analyze_birads_independently") as mock_analyze:
            mock_analyze.return_value = mock_llm_independent_analysis

            with patch("medcrux.api.main.extract_text_from_bytes") as mock_extract:
                mock_extract.return_value = "检查所见：左侧乳腺外上象限距乳头约2.0cm处可见一低回声结节。"

                # 创建测试图片文件
                image_bytes = b"fake image data"
                files = {"file": ("test.jpg", image_bytes, "image/jpeg")}

                # 发送请求
                response = client.post("/api/analyze/upload", files=files)

                # 验证响应
                assert response.status_code == 200
                data = response.json()

                # 验证ai_result包含_new_format
                assert "_new_format" in data["ai_result"]
                new_format = data["ai_result"]["_new_format"]

                # 验证nodules存在
                assert "nodules" in new_format
                assert len(new_format["nodules"]) > 0

                # 验证birads_class字段存在（前端期望的字段）
                nodule = new_format["nodules"][0]
                assert "birads_class" in nodule, "后端必须返回birads_class字段（前端期望的字段）"
                assert nodule["birads_class"] == "3", "birads_class应该等于llm_birads_class的值"

    def test_backend_standardizes_clock_position(self):
        """
        测试后端标准化clock_position（如果LLM返回象限，转换为钟点）
        
        验证：后端标准化逻辑是否正确转换quadrant到clock_position
        """
        # 模拟analyze_birads_independently返回象限而不是钟点
        mock_llm_independent_analysis = {
            "nodules": [
                {
                    "id": "nodule_1",
                    "llm_birads_class": "3",
                    "location": {
                        "breast": "left",
                        "quadrant": "上外",  # LLM返回象限
                        "distance_from_nipple": "2.0",
                    },
                    "morphology": {
                        "shape": "椭圆形",
                        "boundary": "清晰",
                        "echo": "均匀低回声",
                        "orientation": "平行",
                    },
                }
            ],
            "llm_highest_birads": "3",
        }

        with patch("medcrux.api.main.analyze_birads_independently") as mock_analyze:
            mock_analyze.return_value = mock_llm_independent_analysis

            with patch("medcrux.api.main.extract_text_from_bytes") as mock_extract:
                mock_extract.return_value = "检查所见：左侧乳腺外上象限距乳头约2.0cm处可见一低回声结节。"

                # 创建测试图片文件
                image_bytes = b"fake image data"
                files = {"file": ("test.jpg", image_bytes, "image/jpeg")}

                # 发送请求
                response = client.post("/api/analyze/upload", files=files)

                # 验证响应
                assert response.status_code == 200
                data = response.json()

                # 验证ai_result包含_new_format
                assert "_new_format" in data["ai_result"]
                new_format = data["ai_result"]["_new_format"]

                # 验证nodules存在
                assert "nodules" in new_format
                assert len(new_format["nodules"]) > 0

                # 验证clock_position已标准化
                nodule = new_format["nodules"][0]
                assert "location" in nodule
                location = nodule["location"]
                assert "clock_position" in location, "后端必须返回clock_position字段"
                assert location["clock_position"] == "11点", "左乳上外应该转换为11点"
                assert re.match(r"^\d+点$", location["clock_position"]), "clock_position必须是标准格式（X点）"

    def test_quadrant_to_clock_position_conversion(self):
        """
        测试象限到钟点的转换函数
        
        验证：_convert_quadrant_to_clock_position函数是否正确转换
        """
        # 测试左乳
        assert _convert_quadrant_to_clock_position("上外", "left") == "11点"
        assert _convert_quadrant_to_clock_position("外上", "left") == "11点"
        assert _convert_quadrant_to_clock_position("下外", "left") == "7点"
        assert _convert_quadrant_to_clock_position("外下", "left") == "7点"
        assert _convert_quadrant_to_clock_position("上内", "left") == "1点"
        assert _convert_quadrant_to_clock_position("内上", "left") == "1点"
        assert _convert_quadrant_to_clock_position("下内", "left") == "5点"
        assert _convert_quadrant_to_clock_position("内下", "left") == "5点"

        # 测试右乳（镜像）
        assert _convert_quadrant_to_clock_position("上外", "right") == "1点"
        assert _convert_quadrant_to_clock_position("外上", "right") == "1点"
        assert _convert_quadrant_to_clock_position("下外", "right") == "5点"
        assert _convert_quadrant_to_clock_position("外下", "right") == "5点"
        assert _convert_quadrant_to_clock_position("上内", "right") == "11点"
        assert _convert_quadrant_to_clock_position("内上", "right") == "11点"
        assert _convert_quadrant_to_clock_position("下内", "right") == "7点"
        assert _convert_quadrant_to_clock_position("内下", "right") == "7点"

    def test_backend_handles_invalid_clock_position(self):
        """
        测试后端处理非标准clock_position格式
        
        验证：如果LLM返回非标准格式的clock_position，后端应该从quadrant转换
        """
        # 模拟analyze_birads_independently返回非标准格式的clock_position
        mock_llm_independent_analysis = {
            "nodules": [
                {
                    "id": "nodule_1",
                    "llm_birads_class": "3",
                    "location": {
                        "breast": "left",
                        "clock_position": "上外",  # 非标准格式（应该是"11点"）
                        "quadrant": "上外",  # 有quadrant信息
                        "distance_from_nipple": "2.0",
                    },
                    "morphology": {
                        "shape": "椭圆形",
                        "boundary": "清晰",
                        "echo": "均匀低回声",
                        "orientation": "平行",
                    },
                }
            ],
            "llm_highest_birads": "3",
        }

        with patch("medcrux.api.main.analyze_birads_independently") as mock_analyze:
            mock_analyze.return_value = mock_llm_independent_analysis

            with patch("medcrux.api.main.extract_text_from_bytes") as mock_extract:
                mock_extract.return_value = "检查所见：左侧乳腺外上象限距乳头约2.0cm处可见一低回声结节。"

                # 创建测试图片文件
                image_bytes = b"fake image data"
                files = {"file": ("test.jpg", image_bytes, "image/jpeg")}

                # 发送请求
                response = client.post("/api/analyze/upload", files=files)

                # 验证响应
                assert response.status_code == 200
                data = response.json()

                # 验证ai_result包含_new_format
                assert "_new_format" in data["ai_result"]
                new_format = data["ai_result"]["_new_format"]

                # 验证nodules存在
                assert "nodules" in new_format
                assert len(new_format["nodules"]) > 0

                # 验证clock_position已标准化
                nodule = new_format["nodules"][0]
                assert "location" in nodule
                location = nodule["location"]
                assert "clock_position" in location
                assert location["clock_position"] == "11点", "非标准格式应该从quadrant转换为标准格式"
                assert re.match(r"^\d+点$", location["clock_position"]), "clock_position必须是标准格式（X点）"

