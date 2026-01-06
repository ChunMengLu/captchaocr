import os
import time
from typing import Optional
from contextlib import asynccontextmanager

import ddddocr
from fastapi import FastAPI, File, UploadFile, HTTPException
from fastapi.responses import JSONResponse
from pydantic import BaseModel


# 配置项（可通过环境变量覆盖）
LISTEN_HOST = os.getenv("LISTEN_HOST", "0.0.0.0")
PORT = int(os.getenv("PORT", "5000"))
WORKER_THREADS = int(os.getenv("WORKER_THREADS", "10"))

# OCR 实例池
ddddocr_list = []
ddddocr_state = []


def init_ocr_pool():
    """初始化 OCR 实例池"""
    global ddddocr_list, ddddocr_state
    for i in range(WORKER_THREADS):
        ddddocr_list.append(ddddocr.DdddOcr())
        ddddocr_state.append(0)
    print(f"OCR pool initialized with {WORKER_THREADS} workers")


def get_ddddocr() -> int:
    """获取空闲的 OCR 实例索引"""
    for i in range(len(ddddocr_state)):
        if ddddocr_state[i] == 0:
            ddddocr_state[i] = 1
            return i
    return -1


def release_ddddocr(index: int):
    """释放 OCR 实例"""
    if 0 <= index < len(ddddocr_state):
        ddddocr_state[index] = 0


@asynccontextmanager
async def lifespan(app: FastAPI):
    """应用生命周期管理"""
    # 启动时初始化
    init_ocr_pool()
    yield
    # 关闭时清理（如果需要）


app = FastAPI(
    title="Captcha OCR API",
    description="基于 ddddocr 的验证码识别服务",
    version="2.0.0",
    lifespan=lifespan
)


class OCRResponse(BaseModel):
    """OCR 响应模型"""
    status: bool
    msg: str
    result: Optional[str] = None
    usage: Optional[float] = None


@app.get("/")
async def root():
    """健康检查接口"""
    return {
        "status": True,
        "msg": "Captcha OCR Service is running",
        "workers": WORKER_THREADS,
        "available_workers": sum(1 for s in ddddocr_state if s == 0)
    }


@app.post("/ocr", response_model=OCRResponse)
async def ocr(file: UploadFile = File(...)):
    """
    验证码识别接口
    
    - **file**: 图片文件（支持 jpg, png, jpeg 格式）
    """
    # 检查文件类型
    if not file.filename:
        raise HTTPException(status_code=400, detail="文件名不能为空")
    
    file_ext = file.filename.split('.')[-1].lower()
    if file_ext not in ['jpg', 'png', 'jpeg']:
        raise HTTPException(status_code=400, detail="不支持的文件格式，仅支持 jpg, png, jpeg")
    
    try:
        # 读取文件内容
        content = await file.read()
        
        # 获取 OCR 实例
        ocr_index = get_ddddocr()
        if ocr_index == -1:
            raise HTTPException(status_code=503, detail="没有空闲的 OCR 线程，请稍后重试")
        
        try:
            print(f"已调度线程 {ocr_index}")
            start_time = time.time()
            
            # 执行 OCR 识别
            result = ddddocr_list[ocr_index].classification(content)
            
            end_time = time.time()
            usage_time = end_time - start_time
            
            print(f"线程 {ocr_index} 已释放")
            
            return OCRResponse(
                status=True,
                msg="SUCCESS",
                result=result,
                usage=usage_time
            )
        finally:
            release_ddddocr(ocr_index)
            
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"服务器错误: {str(e)}")


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host=LISTEN_HOST, port=PORT)
