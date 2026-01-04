"""
MedCrux API主模块

根据STANDARDS_v1.1.md要求：
- 基础日志记录：记录关键操作和错误
- 错误追踪：所有异常必须被捕获并记录
"""

from fastapi import FastAPI, File, HTTPException, UploadFile
from fastapi.responses import JSONResponse
from pydantic import BaseModel

from medcrux.analysis.llm_engine import analyze_text_with_deepseek
from medcrux.ingestion.ocr_service import extract_text_from_bytes
from medcrux.utils.logger import log_error_with_context, setup_logger

# 初始化logger
logger = setup_logger("medcrux.api")

app = FastAPI(title="MedCrux API", version="0.1.0")


class HealthResponse(BaseModel):
    status: str
    version: str


class AnalysisResponse(BaseModel):
    filename: str
    ocr_text: str
    ai_result: dict
    message: str


@app.get("/health", response_model=HealthResponse)
async def health_check():
    """
    健康检查接口：用于监控系统确认服务是否存活
    """
    logger.info("健康检查请求")
    return {"status": "operational", "version": "1.0.0"}


@app.post("/analyze/upload", response_model=AnalysisResponse)
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

        # 4. AI分析
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

        # 5. 返回结果
        logger.info(f"分析完成 [文件: {file.filename}]")
        return {
            "filename": file.filename,
            "ocr_text": raw_text,
            "ai_result": ai_analysis,
            "message": "分析完成",
        }

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
