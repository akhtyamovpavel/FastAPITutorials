"""
FastAPI Image Handling Example

Demonstrates:
1. File upload with validation
2. Image processing (resize, format conversion)
3. Serving static files
4. Downloading processed images
5. Async file operations
"""

from fastapi import FastAPI, File, UploadFile, HTTPException, status, Query
from fastapi.responses import FileResponse, StreamingResponse
from fastapi.staticfiles import StaticFiles
from pathlib import Path
from PIL import Image
import io
import shutil
from typing import Literal
from pydantic import BaseModel, Field
from contextlib import asynccontextmanager

UPLOAD_DIR = Path("uploads")
PROCESSED_DIR = Path("processed")

class ImageInfo(BaseModel):
    """Image metadata response"""
    filename: str
    size_bytes: int
    format: str = Field(description="Image format (JPEG, PNG, etc.)")
    width: int
    height: int

@asynccontextmanager
async def lifespan(app: FastAPI):
    """Create directories on startup"""
    UPLOAD_DIR.mkdir(exist_ok=True)
    PROCESSED_DIR.mkdir(exist_ok=True)
    yield

app = FastAPI(
    title="Image Handling API",
    description="Upload, process, and download images with FastAPI",
    lifespan=lifespan
)

app.mount("/static", StaticFiles(directory=str(PROCESSED_DIR)), name="static")

@app.post("/upload/", response_model=ImageInfo, status_code=status.HTTP_201_CREATED)
async def upload_image(file: UploadFile = File(...)):
    """
    Upload an image file with validation

    - Validates file type (only images)
    - Saves original file
    - Returns image metadata
    """
    if not file.content_type or not file.content_type.startswith("image/"):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="File must be an image"
        )

    file_path = UPLOAD_DIR / file.filename

    with file_path.open("wb") as buffer:
        shutil.copyfileobj(file.file, buffer)

    with Image.open(file_path) as img:
        return ImageInfo(
            filename=file.filename,
            size_bytes=file_path.stat().st_size,
            format=img.format,
            width=img.width,
            height=img.height
        )

@app.post("/process/resize/")
async def resize_image(
    filename: str,
    width: int = Query(gt=0, le=4000),
    height: int = Query(gt=0, le=4000)
):
    """
    Resize uploaded image to specified dimensions

    - Loads image from uploads
    - Resizes maintaining aspect ratio
    - Saves to processed directory
    """
    input_path = UPLOAD_DIR / filename

    if not input_path.exists():
        raise HTTPException(status_code=404, detail="Image not found")

    output_filename = f"resized_{width}x{height}_{filename}"
    output_path = PROCESSED_DIR / output_filename

    with Image.open(input_path) as img:
        img.thumbnail((width, height), Image.Resampling.LANCZOS)
        img.save(output_path)

    return {
        "message": "Image resized successfully",
        "output_file": output_filename,
        "download_url": f"/download/{output_filename}"
    }

@app.post("/process/convert/")
async def convert_format(
    filename: str,
    format: Literal["JPEG", "PNG", "WEBP"] = "PNG"
):
    """
    Convert image to different format

    - Supports JPEG, PNG, WEBP
    - Handles transparency for PNG
    """
    input_path = UPLOAD_DIR / filename

    if not input_path.exists():
        raise HTTPException(status_code=404, detail="Image not found")

    output_filename = f"{Path(filename).stem}.{format.lower()}"
    output_path = PROCESSED_DIR / output_filename

    with Image.open(input_path) as img:
        if format == "JPEG" and img.mode in ("RGBA", "LA", "P"):
            img = img.convert("RGB")

        img.save(output_path, format=format)

    return {
        "message": f"Image converted to {format}",
        "output_file": output_filename,
        "download_url": f"/download/{output_filename}"
    }

@app.get("/download/{filename}")
async def download_image(filename: str):
    """
    Download processed image

    - Returns file as attachment
    - Proper content-type headers
    """
    file_path = PROCESSED_DIR / filename

    if not file_path.exists():
        raise HTTPException(status_code=404, detail="File not found")

    return FileResponse(
        path=file_path,
        filename=filename,
        media_type="application/octet-stream"
    )

@app.get("/preview/{filename}")
async def preview_image(filename: str):
    """
    Preview image in browser (inline display)
    """
    file_path = PROCESSED_DIR / filename

    if not file_path.exists():
        raise HTTPException(status_code=404, detail="File not found")

    return FileResponse(path=file_path, media_type="image/png")

@app.get("/thumbnail/{filename}")
async def get_thumbnail(filename: str, size: int = Query(default=150, gt=0, le=500)):
    """
    Generate and stream thumbnail on-the-fly

    - Creates thumbnail without saving
    - Streams directly to client
    """
    file_path = UPLOAD_DIR / filename

    if not file_path.exists():
        raise HTTPException(status_code=404, detail="File not found")

    with Image.open(file_path) as img:
        img.thumbnail((size, size), Image.Resampling.LANCZOS)

        img_byte_arr = io.BytesIO()
        img.save(img_byte_arr, format='PNG')
        img_byte_arr.seek(0)

        return StreamingResponse(img_byte_arr, media_type="image/png")

@app.get("/images/")
async def list_images():
    """List all uploaded images"""
    uploads = [f.name for f in UPLOAD_DIR.glob("*") if f.is_file()]
    processed = [f.name for f in PROCESSED_DIR.glob("*") if f.is_file()]

    return {
        "uploaded": uploads,
        "processed": processed
    }

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
