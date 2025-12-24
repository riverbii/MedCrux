from fastapi import FastAPI, File, UploadFile
from pydantic import BaseModel

from medcrux.analysis.llm_engine import analyze_text_with_deepseek

# 引入两大护法
from medcrux.ingestion.ocr_service import extract_text_from_bytes

app = FastAPI(title="MedCrux API", version="0.1.0")


class HealthResponse(BaseModel):
    status: str
    version: str


class AnalysisResponse(BaseModel):
    filename: str
    ocr_text: str  # 新增：把识别到的原话返回给前端看
    risk_level: str
    findings: list[str]
    message: str


@app.get("/health", response_model=HealthResponse)
async def health_check():
    return {"status": "operational", "version": "0.1.0"}


@app.post("/analyze/upload", response_model=AnalysisResponse)
async def analyze_report(file: UploadFile = File(...)):
    """
    真·OCR 分析接口
    """
    # 1. 读取上传文件的内容 (bytes)
    file_bytes = await file.read()

    # 2. 调用 OCR 模块进行识别 (True Logic!)
    print(f"正在分析图片: {file.filename} ...")
    raw_text = extract_text_from_bytes(file_bytes)

    # 3. 打印一下识别结果到终端，方便你自己调试看
    print("------ OCR 识别结果 ------")
    print(raw_text[:200] + "...")  # 只打印前200字
    print("-------------------------")

    # 4. 构造返回结果
    # 注意：risk_level 和 findings 暂时还是假的，因为还没接 LLM
    # 但 ocr_text 是真的了！
    return {
        "filename": file.filename,
        "ocr_text": raw_text,  # 把识别到的字吐回去
        "risk_level": "Pending Analysis (Only OCR done)",
        "findings": [
            "Text Extracted Successfully",
            f"Character count: {len(raw_text)}",
        ],
        "message": "OCR 识别完成，等待接入医学大脑。",
    }


# 修改 AnalysisResponse 以匹配 DeepSeek 的返回结构
class AnalysisResponse(BaseModel):
    filename: str
    ocr_text: str
    ai_result: dict  # 直接把 AI 的 JSON 扔回去
    message: str


@app.get("/health", response_model=HealthResponse)
async def health_check():
    """
    健康检查接口：用于飞书/监控系统确认服务是否存活
    """
    return {"status": "operational", "version": "0.1.0"}


@app.post("/analyze/upload", response_model=AnalysisResponse)
async def analyze_report(file: UploadFile = File(...)):
    # 1. 眼睛看 (OCR)
    file_bytes = await file.read()
    raw_text = extract_text_from_bytes(file_bytes)

    if not raw_text or len(raw_text) < 10:
        return {
            "filename": file.filename,
            "ocr_text": "",
            "ai_result": {},
            "message": "未能识别出有效文字，请上传清晰的图片。",
        }

    # 2. 大脑想 (DeepSeek)
    print("正在调用 DeepSeek 进行推理...")
    ai_analysis = analyze_text_with_deepseek(raw_text)

    # 3. 返回结果
    return {
        "filename": file.filename,
        "ocr_text": raw_text,
        "ai_result": ai_analysis,
        "message": "分析完成",
    }
