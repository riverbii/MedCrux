"""
MedCrux API主模块

根据STANDARDS_v1.1.md要求：
- 基础日志记录：记录关键操作和错误
- 错误追踪：所有异常必须被捕获并记录
"""

import re

from fastapi import FastAPI, File, HTTPException, UploadFile
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from pydantic import BaseModel

from medcrux.analysis.llm_engine import (analyze_birads_independently,
                                         analyze_text_with_deepseek,
                                         calculate_urgency_level,
                                         check_consistency_sets)
from medcrux.analysis.report_structure_parser import (extract_doctor_birads,
                                                      parse_report_structure)
from medcrux.analysis.risk_sign_identifier import (aggregate_risk_signs,
                                                   identify_risk_signs)
from medcrux.ingestion.ocr_service import extract_text_from_bytes
from medcrux.utils.logger import log_error_with_context, setup_logger

# 初始化logger
logger = setup_logger("medcrux.api")


def _convert_quadrant_to_clock_position(quadrant: str, breast: str) -> str | None:
    """
    将象限转换为标准钟点位置（统一使用4个固定钟点：1、11、5、7）
    
    Args:
        quadrant: 象限（如"上外"、"下内"等）
        breast: 乳腺侧（"left"或"right"）
    
    Returns:
        标准钟点位置（如"11点"、"1点"等），如果无法转换则返回None
    """
    if not quadrant:
        return None
    
    # 象限到钟点的映射（统一使用4个固定钟点：1、11、5、7）
    # 左乳：外上→11点，外下→7点，内上→1点，内下→5点
    # 右乳：外上→1点，外下→5点，内上→11点，内下→7点（镜像）
    quadrant_map = {
        "上外": {"left": "11点", "right": "1点"},
        "外上": {"left": "11点", "right": "1点"},
        "下外": {"left": "7点", "right": "5点"},
        "外下": {"left": "7点", "right": "5点"},
        "上内": {"left": "1点", "right": "11点"},
        "内上": {"left": "1点", "right": "11点"},
        "下内": {"left": "5点", "right": "7点"},
        "内下": {"left": "5点", "right": "7点"},
    }
    
    breast_key = "right" if breast.lower() == "right" else "left"
    return quadrant_map.get(quadrant, {}).get(breast_key)


def _match_nodule_by_id_or_location(llm_nodule: dict, original_nodules: list[dict]) -> dict | None:
    """
    通过ID或位置匹配找到对应的原始nodule
    
    Args:
        llm_nodule: LLM独立判断返回的nodule
        original_nodules: 原始分析结果中的nodules列表
    
    Returns:
        匹配到的原始nodule，如果没有匹配则返回None
    """
    llm_id = llm_nodule.get("id")
    llm_location = llm_nodule.get("location", {})
    llm_breast = llm_location.get("breast", "")
    llm_clock_position = llm_location.get("clock_position", "")
    llm_quadrant = llm_location.get("quadrant", "")
    
    # 优先通过ID匹配
    if llm_id:
        for orig_nodule in original_nodules:
            if orig_nodule.get("id") == llm_id:
                return orig_nodule
    
    # 如果ID不匹配，尝试通过位置匹配
    for orig_nodule in original_nodules:
        orig_location = orig_nodule.get("location", {})
        orig_breast = orig_location.get("breast", "")
        orig_clock_position = orig_location.get("clock_position", "")
        orig_quadrant = orig_location.get("quadrant", "")
        
        # 位置匹配：breast和clock_position或quadrant匹配
        if orig_breast == llm_breast:
            if (orig_clock_position and llm_clock_position and orig_clock_position == llm_clock_position) or \
               (orig_quadrant and llm_quadrant and orig_quadrant == llm_quadrant):
                return orig_nodule
    
    return None


def _merge_nodule_data(original_nodule: dict | None, llm_nodule: dict) -> dict:
    """
    合并原始nodule和LLM独立判断的nodule数据
    
    Args:
        original_nodule: 原始分析结果中的nodule（可能为None）
        llm_nodule: LLM独立判断返回的nodule
    
    Returns:
        合并后的标准化nodule
    """
    # 1. 基础数据：优先使用原始nodule，如果没有则使用LLM返回的数据
    if original_nodule:
        standardized_nodule = original_nodule.copy()
    else:
        standardized_nodule = llm_nodule.copy()
    
    # 2. 更新LLM独立判断的BI-RADS分类
    if "llm_birads_class" in llm_nodule:
        standardized_nodule["birads_class"] = llm_nodule["llm_birads_class"]
        standardized_nodule["llm_birads_class"] = llm_nodule["llm_birads_class"]
    
    # 3. 合并morphology：优先使用原始数据，如果LLM有更新则合并
    if original_nodule and original_nodule.get("morphology"):
        standardized_nodule["morphology"] = original_nodule["morphology"].copy()
        if llm_nodule.get("morphology"):
            standardized_nodule["morphology"].update(llm_nodule["morphology"])
    elif llm_nodule.get("morphology"):
        standardized_nodule["morphology"] = llm_nodule["morphology"]
    
    # 4. 保留size：优先使用原始数据
    if original_nodule and original_nodule.get("size"):
        standardized_nodule["size"] = original_nodule["size"]
    elif llm_nodule.get("size"):
        standardized_nodule["size"] = llm_nodule["size"]
    
    # 5. 标准化clock_position（如果LLM返回象限，转换为钟点）
    location = standardized_nodule.get("location", {})
    clock_position = location.get("clock_position", "")
    quadrant = location.get("quadrant", "")
    breast = location.get("breast", "left")
    
    # 如果clock_position不是标准钟点格式（如"X点"），尝试从象限转换
    if clock_position and not re.match(r"^\d+点$", clock_position):
        clock_position = None
    
    # 如果没有有效的clock_position，从象限转换
    if not clock_position and quadrant:
        clock_position = _convert_quadrant_to_clock_position(quadrant, breast)
        if clock_position:
            location["clock_position"] = clock_position
            standardized_nodule["location"] = location
    
    return standardized_nodule


app = FastAPI(title="MedCrux API", version="1.3.0")

# 配置CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000", "http://127.0.0.1:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


class HealthResponse(BaseModel):
    status: str
    version: str


class AnalysisResponse(BaseModel):
    filename: str
    ocr_text: str
    ai_result: dict
    message: str
    report_structure: dict | None = None  # 报告结构解析结果（可选）


@app.get("/api/health", response_model=HealthResponse)
async def health_check():
    """
    健康检查接口：用于监控系统确认服务是否存活
    """
    logger.info("健康检查请求")
    return {"status": "operational", "version": "1.3.0"}


@app.post("/api/analyze/upload", response_model=AnalysisResponse)
async def analyze_report(file: UploadFile = File(...)):
    """
    分析医学影像报告接口

    流程：
    1. OCR识别：从图片中提取文本
    2. AI分析：使用DeepSeek进行医学逻辑分析
    3. 返回结果：包含OCR文本和AI分析结果
    """
    context = {"filename": file.filename, "content_type": file.content_type}
    logger.info(f"收到分析请求 [文件: {file.filename}, 类型: {file.content_type}]")

    try:
        # 1. 读取文件内容
        file_bytes = await file.read()
        logger.debug(f"文件读取成功 [大小: {len(file_bytes)} bytes]")

        # 2. OCR识别
        logger.info("开始OCR识别")
        try:
            raw_text = extract_text_from_bytes(file_bytes)
            logger.info(f"OCR识别完成 [文本长度: {len(raw_text)} 字符]")
        except Exception as e:
            log_error_with_context(logger, e, context={"step": "OCR识别", **context}, operation="OCR识别")
            raise HTTPException(status_code=500, detail=f"OCR识别失败: {str(e)}") from e

        # 3. 验证OCR结果
        if not raw_text or len(raw_text) < 10:
            logger.warning(f"OCR识别结果无效 [文本长度: {len(raw_text)}]")
            return {
                "filename": file.filename,
                "ocr_text": "",
                "ai_result": {},
                "message": "未能识别出有效文字，请上传清晰的图片。",
            }

        # 4. 报告结构解析（提取事实性摘要和结论）
        logger.info("开始报告结构解析")
        report_structure = None
        try:
            report_structure = parse_report_structure(raw_text)
            logger.info("报告结构解析完成")
        except Exception as e:
            log_error_with_context(
                logger,
                e,
                context={"step": "报告结构解析", "ocr_text_length": len(raw_text), **context},
                operation="报告结构解析",
            )
            logger.warning("报告结构解析失败，将使用前端fallback逻辑")

        # 4.5. 提取原报告BI-RADS分类（BL-009新增）
        original_birads_data = None
        original_birads_set = set()
        original_highest_birads = None
        
        if report_structure and report_structure.get("diagnosis"):
            try:
                logger.info("开始提取原报告BI-RADS分类")
                original_birads_data = extract_doctor_birads(report_structure["diagnosis"])
                original_birads_set = original_birads_data.get("birads_set", set())
                original_highest_birads = original_birads_data.get("highest_birads")
                logger.info(
                    f"原报告BI-RADS分类提取完成: 集合={original_birads_set}, 最高={original_highest_birads}"
                )
            except Exception as e:
                log_error_with_context(
                    logger,
                    e,
                    context={"step": "提取原报告BI-RADS分类", **context},
                    operation="提取原报告BI-RADS分类",
                )
                logger.warning("提取原报告BI-RADS分类失败，尝试回退到analyze_text_with_deepseek")
                # 回退方案：使用analyze_text_with_deepseek提取
                try:
                    fallback_analysis = analyze_text_with_deepseek(raw_text)
                    nodules = fallback_analysis.get("nodules", [])
                    if nodules:
                        birads_classes = set()
                        highest_birads_num = 0
                        for nodule in nodules:
                            birads_class = nodule.get("birads_class")
                            if birads_class:
                                birads_classes.add(birads_class)
                                try:
                                    birads_num = int(re.match(r"\d+", birads_class).group())
                                    if birads_num > highest_birads_num:
                                        highest_birads_num = birads_num
                                        original_highest_birads = birads_class
                                except (ValueError, AttributeError):
                                    pass
                        original_birads_set = birads_classes
                        logger.info(f"回退方案提取成功: 集合={original_birads_set}, 最高={original_highest_birads}")
                except Exception as fallback_error:
                    logger.error(f"回退方案也失败: {fallback_error}")

        # 5. AI分析（保留现有流程，用于向后兼容）
        logger.info("开始AI分析")
        try:
            ai_analysis = analyze_text_with_deepseek(raw_text)
            logger.info("AI分析完成")
            logger.debug(f"AI分析结果: {ai_analysis.get('ai_risk_assessment', 'Unknown')}")
        except Exception as e:
            log_error_with_context(
                logger, e, context={"step": "AI分析", "ocr_text_length": len(raw_text), **context}, operation="AI分析"
            )
            # AI分析失败时，返回OCR结果和错误信息
            return {
                "filename": file.filename,
                "ocr_text": raw_text,
                "ai_result": {
                    "ai_risk_assessment": "Error",
                    "advice": "AI分析失败，请稍后重试。",
                    "error": str(e),
                },
                "message": "OCR识别完成，但AI分析失败。",
            }

        # 5.5. LLM请求2：基于findings独立判断BI-RADS分类（BL-009新增）
        llm_independent_analysis = None
        llm_birads_set = set()
        llm_highest_birads = None
        
        if report_structure and report_structure.get("findings"):
            try:
                logger.info("开始独立BI-RADS判断")
                llm_independent_analysis = analyze_birads_independently(report_structure["findings"])
                nodules = llm_independent_analysis.get("nodules", [])
                llm_highest_birads = llm_independent_analysis.get("llm_highest_birads")
                
                # 提取AI判断的BI-RADS分类集合
                for nodule in nodules:
                    birads_class = nodule.get("llm_birads_class")
                    if birads_class:
                        llm_birads_set.add(birads_class)
                
                logger.info(
                    f"独立BI-RADS判断完成: 集合={llm_birads_set}, 最高={llm_highest_birads}, "
                    f"异常发现数={len(nodules)}"
                )
            except Exception as e:
                log_error_with_context(
                    logger,
                    e,
                    context={"step": "独立BI-RADS判断", **context},
                    operation="独立BI-RADS判断",
                )
                logger.warning("独立BI-RADS判断失败，将跳过BL-009相关功能")

        # 5.6. 一致性校验（BL-009新增）
        consistency_result = None
        if original_birads_set and llm_birads_set:
            try:
                logger.info("开始一致性校验")
                consistency_result = check_consistency_sets(original_birads_set, llm_birads_set)
                logger.info(f"一致性校验完成: 一致={consistency_result.get('consistent')}")
            except Exception as e:
                log_error_with_context(logger, e, context={"step": "一致性校验", **context}, operation="一致性校验")
                logger.warning("一致性校验失败")

        # 5.7. 计算评估紧急程度（BL-009新增）
        assessment_urgency = None
        if original_highest_birads and llm_highest_birads:
            try:
                logger.info("开始计算评估紧急程度")
                assessment_urgency = calculate_urgency_level(original_highest_birads, llm_highest_birads)
                logger.info(f"评估紧急程度计算完成: {assessment_urgency.get('urgency_level')}")
            except Exception as e:
                log_error_with_context(
                    logger, e, context={"step": "计算评估紧急程度", **context}, operation="计算评估紧急程度"
                )
                logger.warning("计算评估紧急程度失败")

        # 5.8. 合并结果（BL-009新增）
        # 优先使用独立BI-RADS判断的结果，如果没有则使用原有分析结果
        if llm_independent_analysis and llm_independent_analysis.get("nodules"):
            # 获取原有nodules（包含完整的size和morphology信息）
            original_nodules = ai_analysis.get("nodules", [])
            
            # 标准化和映射数据
            standardized_nodules = []
            for llm_nodule in llm_independent_analysis["nodules"]:
                # 匹配原始nodule
                matched_original = _match_nodule_by_id_or_location(llm_nodule, original_nodules)
                
                # 合并数据（参数顺序：original_nodule, llm_nodule）
                standardized_nodule = _merge_nodule_data(matched_original, llm_nodule)
                standardized_nodules.append(standardized_nodule)
            
            # 使用合并后的nodules更新ai_analysis
            ai_analysis["nodules"] = standardized_nodules
            
            # 如果独立判断提供了llm_highest_birads，也更新
            if llm_independent_analysis.get("llm_highest_birads"):
                if "overall_assessment" not in ai_analysis:
                    ai_analysis["overall_assessment"] = {}
                # 可以在这里更新overall_assessment中的highest_risk等信息
        
        # 5.9. 风险征兆识别（BL-010新增）
        # 为每个异常发现识别风险征兆
        if ai_analysis.get("nodules"):
            try:
                logger.info("开始风险征兆识别")
                findings_text = report_structure.get("findings", "") if report_structure else ""
                
                for nodule in ai_analysis["nodules"]:
                    morphology = nodule.get("morphology", {})
                    risk_signs = identify_risk_signs(morphology, findings_text)
                    if risk_signs:
                        nodule["risk_signs"] = risk_signs
                        logger.debug(f"异常发现 {nodule.get('id', 'unknown')} 识别到 {len(risk_signs)} 个风险征兆")
                
                # 汇总所有风险征兆
                risk_signs_summary = aggregate_risk_signs(ai_analysis["nodules"])
                if risk_signs_summary["strong_evidence"] or risk_signs_summary["weak_evidence"]:
                    if "overall_assessment" not in ai_analysis:
                        ai_analysis["overall_assessment"] = {}
                    ai_analysis["overall_assessment"]["risk_signs_summary"] = risk_signs_summary
                    logger.info(
                        f"风险征兆汇总完成: 强证据={len(risk_signs_summary['strong_evidence'])}, "
                        f"弱证据={len(risk_signs_summary['weak_evidence'])}"
                    )
            except Exception as e:
                log_error_with_context(
                    logger, e, context={"step": "风险征兆识别", **context}, operation="风险征兆识别"
                )
                logger.warning("风险征兆识别失败，将继续处理")
        
        # 添加BL-009相关结果
        if assessment_urgency:
            ai_analysis["assessment_urgency"] = assessment_urgency
        if consistency_result:
            ai_analysis["consistency_check"] = consistency_result

        # 6. 格式适配：为了向后兼容，将新格式转换为旧格式（临时方案，阶段2会更新UI）
        # 新格式：{"nodules": [...], "overall_assessment": {...}}
        # 旧格式：{"extracted_shape": "...", "ai_risk_assessment": "...", ...}
        def convert_new_to_old_format(new_result: dict) -> dict:
            """将新格式（结节列表）转换为旧格式（单一结果），用于UI向后兼容"""
            # 如果已经是旧格式，直接返回
            if "extracted_shape" in new_result or "nodules" not in new_result:
                return new_result

            # 获取第一个结节（如果有）
            nodules = new_result.get("nodules", [])
            overall_assessment = new_result.get("overall_assessment", {})

            if not nodules:
                # 无结节情况
                return {
                    "patient_gender": new_result.get("patient_gender", "Unknown"),
                    "extracted_findings": overall_assessment.get("summary", []),
                    "extracted_shape": "未提取",
                    "extracted_boundary": "未提取",
                    "extracted_echo": "未提取",
                    "extracted_orientation": "未提取",
                    "extracted_malignant_signs": [],
                    "original_conclusion": "",
                    "birads_class": "",
                    "ai_risk_assessment": overall_assessment.get("highest_risk", "Low"),
                    "inconsistency_alert": False,
                    "inconsistency_reasons": [],
                    "advice": overall_assessment.get("advice", ""),
                }

            # 使用第一个结节的数据
            first_nodule = nodules[0]
            morphology = first_nodule.get("morphology", {})

            return {
                "patient_gender": new_result.get("patient_gender", "Unknown"),
                "extracted_findings": overall_assessment.get("summary", []),
                "extracted_shape": morphology.get("shape", ""),
                "extracted_boundary": morphology.get("boundary", ""),
                "extracted_echo": morphology.get("echo", ""),
                "extracted_orientation": morphology.get("orientation", ""),
                "extracted_malignant_signs": first_nodule.get("malignant_signs", []),
                "original_conclusion": "",
                "birads_class": first_nodule.get("birads_class", ""),
                "ai_risk_assessment": overall_assessment.get(
                    "highest_risk", first_nodule.get("risk_assessment", "Low")
                ),
                "inconsistency_alert": first_nodule.get("inconsistency_alert", False),
                "inconsistency_reasons": first_nodule.get("inconsistency_reasons", []),
                "advice": overall_assessment.get("advice", ""),
                # 保留新格式数据，供阶段2使用（包含风险征兆数据）
                "_new_format": new_result,
                # 添加报告结构解析结果（如果可用）
                "_report_structure": report_structure,
            }

        ai_result_for_ui = convert_new_to_old_format(ai_analysis)

        # 7. 返回结果（包含报告结构解析结果）
        logger.info(f"分析完成 [文件: {file.filename}]")
        response_data = {
            "filename": file.filename,
            "ocr_text": raw_text,
            "ai_result": ai_result_for_ui,
            "message": "分析完成",
        }

        # 如果报告结构解析成功，添加到响应中
        if report_structure:
            response_data["report_structure"] = report_structure

        return response_data

    except HTTPException:
        # HTTPException直接抛出
        raise
    except Exception as e:
        # 捕获所有未预期的异常
        log_error_with_context(logger, e, context=context, operation="报告分析")
        raise HTTPException(status_code=500, detail=f"分析过程中发生错误: {str(e)}") from e


@app.exception_handler(Exception)
async def global_exception_handler(request, exc):
    """
    全局异常处理器：捕获所有未处理的异常
    """
    log_error_with_context(
        logger, exc, context={"path": str(request.url), "method": request.method}, operation="全局异常处理"
    )
    return JSONResponse(status_code=500, content={"detail": "服务器内部错误，请稍后重试。"})
