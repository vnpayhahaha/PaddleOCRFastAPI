# -*- coding: utf-8 -*-

# import uvicorn
from fastapi import FastAPI, Request, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
# import uvicorn
import yaml

from models.RestfulModel import *
from routers import ocr
from utils.ImageHelper import *

app = FastAPI(title="Paddle OCR API",
              description="基于 Paddle OCR 和 FastAPI 的自用接口")


# 跨域设置
origins = [
    "*"
]
app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"]
)


# 全局异常处理器 - 处理参数验证错误
@app.exception_handler(RequestValidationError)
async def validation_exception_handler(request: Request, exc: RequestValidationError):
    """
    捕获 Pydantic 参数验证错误,统一返回 RestfulModel 格式
    """
    # 提取错误信息
    errors = exc.errors()
    error_messages = []
    for error in errors:
        field = " -> ".join(str(loc) for loc in error["loc"])
        msg = error["msg"]
        error_messages.append(f"{field}: {msg}")

    error_detail = "; ".join(error_messages)

    return JSONResponse(
        status_code=status.HTTP_200_OK,  # 返回 200 状态码,但 resultcode 为 400
        content={
            "resultcode": 400,
            "success": False,
            "message": f"参数验证失败: {error_detail}",
            "data": []
        }
    )


# 全局异常处理器 - 处理其他 HTTP 异常
@app.exception_handler(Exception)
async def general_exception_handler(request: Request, exc: Exception):
    """
    捕获未处理的异常,统一返回 RestfulModel 格式
    """
    return JSONResponse(
        status_code=status.HTTP_200_OK,  # 返回 200 状态码,但 resultcode 为 500
        content={
            "resultcode": 500,
            "success": False,
            "message": f"服务器内部错误: {str(exc)}",
            "data": []
        }
    )


app.include_router(ocr.router)

# uvicorn.run(app=app, host="0.0.0.0", port=8000)
