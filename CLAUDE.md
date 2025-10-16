# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## User Preferences

**IMPORTANT: Always communicate with the user in Chinese (中文).** The repository owner prefers Chinese for all interactions, explanations, and discussions.

## Project Overview

PaddleOCRFastAPI is a FastAPI-based web service that wraps PaddleOCR (Baidu's OCR engine) to provide REST API endpoints for text recognition from images. The service supports multiple input methods (local paths, base64, file uploads, URLs) and can recognize text in 80+ languages.

**Tech Stack:**
- FastAPI 0.101.0 (async Python web framework)
- PaddleOCR 2.7.0.0 (OCR engine)
- PaddlePaddle 2.6.2 (deep learning framework)
- Uvicorn 0.23.2 (ASGI server)
- Python 3.8+

## Development Commands

### Running the Application

**Direct execution:**
```bash
uvicorn main:app --host 0.0.0.0 --port 8000
```

**With custom workers and logging:**
```bash
uvicorn main:app --host 0.0.0.0 --workers 2 --log-config ./log_conf.yaml
```

**Access Swagger API docs:**
```
http://localhost:8000/docs
```

### Dependency Management

**Install dependencies:**
```bash
pip3 install -r requirements.txt
```

**Update pinned dependencies (uses pip-compile):**
```bash
pip-compile requirements.in > requirements.txt
```

### Docker Commands

**Download OCR models (required before first build):**
```bash
cd pp-ocrv4/
sh download_det_cls_rec.sh
cd ..
```

**Build Docker image:**
```bash
docker build -t paddleocrfastapi:latest --network host .
```

**Build with proxy (if needed):**
```bash
docker build -t paddleocrfastapi:latest --network host \
  --build-arg HTTP_PROXY=http://127.0.0.1:8888 \
  --build-arg HTTPS_PROXY=http://127.0.0.1:8888 .
```

**Run with Docker Compose:**
```bash
docker compose up -d
```

**Stop container:**
```bash
docker compose down
```

## Architecture

### Application Structure

```
main.py                    # FastAPI app entry point, CORS config, router registration
├── routers/
│   └── ocr.py            # OCR endpoints, PaddleOCR initialization
├── models/
│   ├── RestfulModel.py   # API response schema (resultcode, message, data)
│   └── OCRModel.py       # OCR result schema and Base64PostModel
└── utils/
    └── ImageHelper.py    # Image format conversions (base64/bytes → numpy)
```

### Key Design Patterns

**Single PaddleOCR Instance:** The OCR engine is initialized once at module load in `routers/ocr.py:15` and reused across all requests. This is critical for performance as initialization is expensive.

**Image Processing Pipeline:** All endpoints follow the same flow:
1. Input → Image conversion (via ImageHelper utilities)
2. Convert to numpy array (required by PaddleOCR)
3. OCR processing with angle classification enabled (`cls=True`)
4. Wrap result in RestfulModel response

**Three-stage OCR:** PaddleOCR uses three models stored in `/root/.paddleocr/whl/`:
- Detection model (`det/ch/`) - Locates text regions
- Classification model (`cls/`) - Corrects text orientation
- Recognition model (`rec/ch/`) - Extracts text content

### API Endpoints

All routes are prefixed with `/ocr`:

1. **GET /ocr/predict-by-path** - Process local filesystem images (useful for server-side files)
2. **POST /ocr/predict-by-base64** - Process base64-encoded images (common for web apps)
3. **POST /ocr/predict-by-file** - Upload and process image files (multipart/form-data)
4. **GET /ocr/predict-by-url** - Download and process remote images

**Response Format (Unified):**
```json
{
  "resultcode": 200,
  "success": true,
  "message": "Success",
  "data": ["TransactionSuccessful", "AnotherText", ...]
}
```

- **Success case:** `resultcode=200`, `success=true`, `data` contains array of recognized text strings
- **Error case:** `resultcode=500`, `success=false`, `message` contains error description, `data=[]`

**Data Format Changes:**
- **Previous format:** Complex nested structure with coordinates, text, and confidence: `[[[x1,y1],[x2,y2],[x3,y3],[x4,y4]], ["text", 0.996]]`
- **Current format:** Simplified array of text only: `["text1", "text2", ...]`
- The `extract_text_only()` helper function in `routers/ocr.py:18` extracts only the recognized text, discarding coordinates and confidence scores.

**Image validation:** Only JPEG and PNG formats are accepted. URL endpoint validates using magic bytes (`\xff\xd8\xff` for JPEG, `\x89PNG\r\n\x1a\n` for PNG).

**Error Handling:** All endpoints now use try-except blocks to catch exceptions and return proper error responses with `resultcode=500` and error message.

### Environment Configuration

**OCR_LANGUAGE** (default: "ch"): Controls PaddleOCR language model. Read in `routers/ocr.py:11`. Supports 80+ languages - see [PaddleOCR language list](https://github.com/PaddlePaddle/PaddleOCR/blob/release/2.7/doc/doc_en/multi_languages_en.md#5-support-languages-and-abbreviations).

**TZ** (Docker only): Container timezone setting.

To change language:
1. Set `OCR_LANGUAGE` environment variable, OR
2. Edit `routers/ocr.py:11` and modify the `OCR_LANGUAGE` default value
3. Rebuild Docker image or restart the application

### Logging

Configured via `log_conf.yaml`:
- **uvicorn.error** logs to stderr with timestamp format
- **uvicorn.access** logs to stdout
- Root logger at DEBUG level
- Format: `%(asctime)s - %(name)s - %(levelname)s - %(message)s`

## Version Support

The repository maintains branches for different PaddleOCR versions:
- **master** - PaddleOCR v2.7 (current)
- **paddleocr-v2.7** - PaddleOCR v2.7
- **paddleocr-v2.5** - PaddleOCR v2.5

## Common Development Patterns

### Adding a New OCR Endpoint

1. Define route in `routers/ocr.py` using `@router` decorator
2. Convert input to numpy array using `ImageHelper` utilities
3. Call `ocr.ocr(img, cls=True)` with angle classification
4. Return `RestfulModel(resultcode=200, message="Success", data=result)`

### Modifying Response Format

Edit `models/RestfulModel.py` - all endpoints use this schema. The `RestfulModel` class uses Pydantic for validation:
- `resultcode`: HTTP-like status code (200 for success, 500 for errors)
- `success`: Boolean flag indicating success/failure
- `message`: Human-readable message
- `data`: OCR results - simplified array of text strings (e.g., `["text1", "text2"]`)

**Note:** The response format has been unified across all endpoints. Errors now return `resultcode=500` (not 400) with `success=false`.

### Working with Images

Use utilities in `utils/ImageHelper.py`:
- `base64_to_ndarray(b64_data)` - Decode base64 string to OpenCV-compatible numpy array
- `bytes_to_ndarray(img_bytes)` - Convert raw bytes to numpy array

Both functions return images in the format expected by PaddleOCR (numpy ndarray).

## Deployment Considerations

### Model Files

PaddleOCR models are stored in `/root/.paddleocr/whl/` (Docker) or `~/.paddleocr/whl/` (direct install). The Dockerfile pre-extracts models from `pp-ocrv4/*.tar` archives to avoid first-run downloads. This enables fully offline deployment.

**Manual model download is recommended** before Docker build to:
- Speed up container startup
- Enable offline deployment
- Avoid network issues during first run

### Resource Requirements

- **CPU Mode:** Default configuration (GPU support not yet implemented)
- **Workers:** Dockerfile uses 2 workers, adjust based on CPU cores
- **Memory:** PaddlePaddle models require ~500MB+ RAM per worker

### Tested Platforms

Docker deployment verified on:
- CentOS 7
- Ubuntu 20.04, 22.04
- Windows 10, 11

### Network Configuration

The Dockerfile uses `--network host` during build to leverage host network settings (useful for proxies). The CORS middleware in `main.py` allows all origins (`*`) - restrict this in production.

## Known Limitations

1. **No GPU support** - Currently CPU-only (GPU mode is in TODO)
2. **No tests** - `.gitignore` excludes `test.py` but no test suite exists
3. **CORS fully open** - All origins allowed, should be restricted for production
4. **No rate limiting** - Consider adding for production deployments
5. **No auth** - Endpoints are publicly accessible
6. **Simplified output** - Coordinates and confidence scores are not included in API responses (only text strings)

## File Locations to Remember

- **PaddleOCR initialization:** `routers/ocr.py:15` - Only place where OCR engine is instantiated
- **Text extraction helper:** `routers/ocr.py:18` - `extract_text_only()` function simplifies OCR output
- **Language configuration:** `routers/ocr.py:11` - Environment variable read
- **Image format validation:** `routers/ocr.py:69` (file upload), `routers/ocr.py:103` (URL)
- **Response model definition:** `models/RestfulModel.py:10` - Shared by all endpoints (includes `success` field)
- **Model extraction in Docker:** `Dockerfile:35-41` - Model setup for offline deployment
- **CORS configuration:** `main.py` - Middleware setup with allow_origins=["*"]
