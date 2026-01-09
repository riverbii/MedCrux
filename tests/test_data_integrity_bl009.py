"""
BL-009 数据完整性测试

测试目标：
1. 验证后端返回的所有关键字段都能正确传递到前端
2. 验证字段映射正确性（llm_birads_class → birads_class等）
3. 验证数据合并逻辑不会丢失size和morphology字段

基于：docs/gov/QA_DATA_INTEGRITY_TEST_GUIDE.md
"""

import json
import pytest
from fastapi.testclient import TestClient
from unittest.mock import patch, MagicMock

from medcrux.api.main import app

client = TestClient(app)


class TestDataIntegrityBL009:
    """BL-009数据完整性测试类"""

    def test_backend_nodules_contains_size(self):
        """测试后端返回的nodules包含size字段"""
        # Mock数据
        mock_ai_analysis = {
            "nodules": [
                {
                    "id": "nodule_1",
                    "name": "异常发现1",
                    "location": {"breast": "left", "clock_position": "11点"},
                    "size": {"length": 1.0, "width": 0.8, "depth": 0.6},
                    "morphology": {"shape": "椭圆形", "boundary": "清晰"},
                    "birads_class": "3",
                    "risk_assessment": "Low",
                }
            ],
            "overall_assessment": {"summary": "测试摘要"},
        }

        mock_llm_independent = {
            "nodules": [
                {
                    "id": "nodule_1",
                    "location": {"breast": "left", "clock_position": "11点"},
                    "llm_birads_class": "3",
                }
            ],
            "llm_highest_birads": "3",
        }

        with patch("medcrux.api.main.extract_text_from_bytes") as mock_extract, \
             patch("medcrux.api.main.parse_report_structure") as mock_parse, \
             patch("medcrux.api.main.analyze_text_with_deepseek") as mock_analyze, \
             patch("medcrux.api.main.analyze_birads_independently") as mock_independent, \
             patch("medcrux.api.main.extract_doctor_birads") as mock_extract_birads:

            mock_extract.return_value = "测试OCR文本"
            mock_parse.return_value = {"findings": "测试findings", "diagnosis": "BI-RADS 3类"}
            mock_analyze.return_value = mock_ai_analysis
            mock_independent.return_value = mock_llm_independent
            mock_extract_birads.return_value = {
                "birads_set": {"3"},
                "birads_list": ["3"],
                "highest_birads": "3",
            }

            # 调用API
            test_image = b"fake_image_data"
            response = client.post("/api/analyze/upload", files={"file": ("test.jpg", test_image, "image/jpeg")})

            assert response.status_code == 200
            result = response.json()

            # 验证后端返回的nodules包含size字段
            nodules = result["ai_result"]["_new_format"]["nodules"]
            assert len(nodules) > 0, "nodules数组应该不为空"

            for nodule in nodules:
                assert "size" in nodule, f"nodule {nodule.get('id')} 应该包含size字段"
                size = nodule["size"]
                assert "length" in size, f"nodule {nodule.get('id')} size应该包含length字段"
                assert "width" in size, f"nodule {nodule.get('id')} size应该包含width字段"
                assert "depth" in size, f"nodule {nodule.get('id')} size应该包含depth字段"

    def test_backend_nodules_contains_morphology(self):
        """测试后端返回的nodules包含morphology字段"""
        # Mock数据
        mock_ai_analysis = {
            "nodules": [
                {
                    "id": "nodule_1",
                    "name": "异常发现1",
                    "location": {"breast": "left", "clock_position": "11点"},
                    "size": {"length": 1.0, "width": 0.8, "depth": 0.6},
                    "morphology": {"shape": "椭圆形", "boundary": "清晰"},
                    "birads_class": "3",
                    "risk_assessment": "Low",
                }
            ],
            "overall_assessment": {"summary": "测试摘要"},
        }

        mock_llm_independent = {
            "nodules": [
                {
                    "id": "nodule_1",
                    "location": {"breast": "left", "clock_position": "11点"},
                    "llm_birads_class": "3",
                }
            ],
            "llm_highest_birads": "3",
        }

        with patch("medcrux.api.main.extract_text_from_bytes") as mock_extract, \
             patch("medcrux.api.main.parse_report_structure") as mock_parse, \
             patch("medcrux.api.main.analyze_text_with_deepseek") as mock_analyze, \
             patch("medcrux.api.main.analyze_birads_independently") as mock_independent, \
             patch("medcrux.api.main.extract_doctor_birads") as mock_extract_birads:

            mock_extract.return_value = "测试OCR文本"
            mock_parse.return_value = {"findings": "测试findings", "diagnosis": "BI-RADS 3类"}
            mock_analyze.return_value = mock_ai_analysis
            mock_independent.return_value = mock_llm_independent
            mock_extract_birads.return_value = {
                "birads_set": {"3"},
                "birads_list": ["3"],
                "highest_birads": "3",
            }

            # 调用API
            test_image = b"fake_image_data"
            response = client.post("/api/analyze/upload", files={"file": ("test.jpg", test_image, "image/jpeg")})

            assert response.status_code == 200
            result = response.json()

            # 验证后端返回的nodules包含morphology字段
            nodules = result["ai_result"]["_new_format"]["nodules"]
            assert len(nodules) > 0, "nodules数组应该不为空"

            for nodule in nodules:
                assert "morphology" in nodule, f"nodule {nodule.get('id')} 应该包含morphology字段"
                morphology = nodule["morphology"]
                assert "shape" in morphology, f"nodule {nodule.get('id')} morphology应该包含shape字段"

    def test_data_merge_preserves_size_and_morphology(self):
        """测试数据合并逻辑不会丢失size和morphology字段"""
        # Mock数据：原有analysis包含完整的size和morphology
        mock_ai_analysis = {
            "nodules": [
                {
                    "id": "nodule_1",
                    "name": "异常发现1",
                    "location": {"breast": "left", "clock_position": "11点"},
                    "size": {"length": 1.0, "width": 0.8, "depth": 0.6},
                    "morphology": {"shape": "椭圆形", "boundary": "清晰", "echo": "均匀低回声"},
                    "birads_class": "3",
                    "risk_assessment": "Low",
                }
            ],
            "overall_assessment": {"summary": "测试摘要"},
        }

        # Mock数据：llm_independent只包含birads_class，不包含size和morphology
        mock_llm_independent = {
            "nodules": [
                {
                    "id": "nodule_1",
                    "location": {"breast": "left", "clock_position": "11点"},
                    "llm_birads_class": "3",
                    # 注意：这里没有size和morphology
                }
            ],
            "llm_highest_birads": "3",
        }

        with patch("medcrux.api.main.extract_text_from_bytes") as mock_extract, \
             patch("medcrux.api.main.parse_report_structure") as mock_parse, \
             patch("medcrux.api.main.analyze_text_with_deepseek") as mock_analyze, \
             patch("medcrux.api.main.analyze_birads_independently") as mock_independent, \
             patch("medcrux.api.main.extract_doctor_birads") as mock_extract_birads:

            mock_extract.return_value = "测试OCR文本"
            mock_parse.return_value = {"findings": "测试findings", "diagnosis": "BI-RADS 3类"}
            mock_analyze.return_value = mock_ai_analysis
            mock_independent.return_value = mock_llm_independent
            mock_extract_birads.return_value = {
                "birads_set": {"3"},
                "birads_list": ["3"],
                "highest_birads": "3",
            }

            # 调用API
            test_image = b"fake_image_data"
            response = client.post("/api/analyze/upload", files={"file": ("test.jpg", test_image, "image/jpeg")})

            assert response.status_code == 200
            result = response.json()

            # 验证合并后的nodules仍然包含size和morphology
            nodules = result["ai_result"]["_new_format"]["nodules"]
            assert len(nodules) > 0, "nodules数组应该不为空"

            nodule = nodules[0]
            # 验证size字段没有被丢失
            assert "size" in nodule, "合并后应该保留size字段"
            assert nodule["size"]["length"] == 1.0, "size.length应该保持不变"
            assert nodule["size"]["width"] == 0.8, "size.width应该保持不变"
            assert nodule["size"]["depth"] == 0.6, "size.depth应该保持不变"

            # 验证morphology字段没有被丢失
            assert "morphology" in nodule, "合并后应该保留morphology字段"
            assert nodule["morphology"]["shape"] == "椭圆形", "morphology.shape应该保持不变"
            assert nodule["morphology"]["boundary"] == "清晰", "morphology.boundary应该保持不变"
            assert nodule["morphology"]["echo"] == "均匀低回声", "morphology.echo应该保持不变"

            # 验证birads_class被正确更新
            assert nodule["birads_class"] == "3", "birads_class应该被更新为llm_birads_class的值"

    def test_field_mapping_llm_birads_to_birads(self):
        """测试llm_birads_class正确映射到birads_class"""
        # Mock数据
        mock_ai_analysis = {
            "nodules": [
                {
                    "id": "nodule_1",
                    "name": "异常发现1",
                    "location": {"breast": "left", "clock_position": "11点"},
                    "size": {"length": 1.0, "width": 0.8, "depth": 0.6},
                    "morphology": {"shape": "椭圆形"},
                    "birads_class": "2",  # 原有birads_class
                    "risk_assessment": "Low",
                }
            ],
            "overall_assessment": {"summary": "测试摘要"},
        }

        mock_llm_independent = {
            "nodules": [
                {
                    "id": "nodule_1",
                    "location": {"breast": "left", "clock_position": "11点"},
                    "llm_birads_class": "3",  # LLM独立判断的birads_class
                }
            ],
            "llm_highest_birads": "3",
        }

        with patch("medcrux.api.main.extract_text_from_bytes") as mock_extract, \
             patch("medcrux.api.main.parse_report_structure") as mock_parse, \
             patch("medcrux.api.main.analyze_text_with_deepseek") as mock_analyze, \
             patch("medcrux.api.main.analyze_birads_independently") as mock_independent, \
             patch("medcrux.api.main.extract_doctor_birads") as mock_extract_birads:

            mock_extract.return_value = "测试OCR文本"
            mock_parse.return_value = {"findings": "测试findings", "diagnosis": "BI-RADS 3类"}
            mock_analyze.return_value = mock_ai_analysis
            mock_independent.return_value = mock_llm_independent
            mock_extract_birads.return_value = {
                "birads_set": {"3"},
                "birads_list": ["3"],
                "highest_birads": "3",
            }

            # 调用API
            test_image = b"fake_image_data"
            response = client.post("/api/analyze/upload", files={"file": ("test.jpg", test_image, "image/jpeg")})

            assert response.status_code == 200
            result = response.json()

            # 验证llm_birads_class正确映射到birads_class
            nodules = result["ai_result"]["_new_format"]["nodules"]
            nodule = nodules[0]
            assert nodule["birads_class"] == "3", "birads_class应该被更新为llm_birads_class的值（3）"
            assert nodule.get("llm_birads_class") == "3", "应该保留llm_birads_class字段"

