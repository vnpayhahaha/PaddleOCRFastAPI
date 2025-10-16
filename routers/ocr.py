# -*- coding: utf-8 -*-

from fastapi import APIRouter, HTTPException, UploadFile, status
from models.OCRModel import *
from models.RestfulModel import *
from paddleocr import PaddleOCR
from utils.ImageHelper import base64_to_ndarray, bytes_to_ndarray
import requests
import os

OCR_LANGUAGE = os.environ.get("OCR_LANGUAGE", "ch")

router = APIRouter(prefix="/ocr", tags=["OCR"])

ocr = PaddleOCR(use_angle_cls=True, lang=OCR_LANGUAGE)


def extract_text_only(ocr_result):
    """提取OCR结果中的文本内容，忽略坐标和置信度"""
    if not ocr_result or not ocr_result[0]:
        return []
    return [line[1][0] for line in ocr_result[0] if line and len(line) > 1]


@router.get('/predict-by-path', response_model=RestfulModel, summary="识别本地图片")
def predict_by_path(image_path: str):
    try:
        result = ocr.ocr(image_path, cls=True)
        text_list = extract_text_only(result)
        return RestfulModel(
            resultcode=200,
            success=True,
            message="Success",
            data=text_list
        )
    except Exception as e:
        return RestfulModel(
            resultcode=500,
            success=False,
            message=str(e),
            data=[]
        )


@router.post('/predict-by-base64', response_model=RestfulModel, summary="识别 Base64 数据")
def predict_by_base64(base64model: Base64PostModel):
    try:
        img = base64_to_ndarray(base64model.base64_str)
        result = ocr.ocr(img=img, cls=True)
        text_list = extract_text_only(result)
        return RestfulModel(
            resultcode=200,
            success=True,
            message="Success",
            data=text_list
        )
    except Exception as e:
        return RestfulModel(
            resultcode=500,
            success=False,
            message=str(e),
            data=[]
        )


@router.post('/predict-by-file', response_model=RestfulModel, summary="识别上传文件")
async def predict_by_file(file: UploadFile):
    try:
        if not file.filename.endswith((".jpg", ".png")):
            return RestfulModel(
                resultcode=500,
                success=False,
                message="请上传 .jpg 或 .png 格式图片",
                data=[]
            )

        file_data = file.file
        file_bytes = file_data.read()
        img = bytes_to_ndarray(file_bytes)
        result = ocr.ocr(img=img, cls=True)
        text_list = extract_text_only(result)
        return RestfulModel(
            resultcode=200,
            success=True,
            message="Success",
            data=text_list
        )
    except Exception as e:
        return RestfulModel(
            resultcode=500,
            success=False,
            message=str(e),
            data=[]
        )


@router.get('/predict-by-url', response_model=RestfulModel, summary="识别图片 URL")
async def predict_by_url(imageUrl: str):
    try:
        response = requests.get(imageUrl)
        image_bytes = response.content

        if not (image_bytes.startswith(b"\xff\xd8\xff") or image_bytes.startswith(b"\x89PNG\r\n\x1a\n")):
            return RestfulModel(
                resultcode=500,
                success=False,
                message="请上传 .jpg 或 .png 格式图片",
                data=[]
            )

        img = bytes_to_ndarray(image_bytes)
        result = ocr.ocr(img=img, cls=True)
        text_list = extract_text_only(result)
        return RestfulModel(
            resultcode=200,
            success=True,
            message="Success",
            data=text_list
        )
    except Exception as e:
        return RestfulModel(
            resultcode=500,
            success=False,
            message=str(e),
            data=[]
        )
