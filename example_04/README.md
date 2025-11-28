**[🇷🇺 Русская версия](README_RU.md)**

# Example 04: Image Handling in FastAPI

## 📚 What You'll Learn

- ✅ **File Upload** - file upload with validation
- ✅ **Image Processing** - image processing (resize, convert)
- ✅ **PIL/Pillow** - working with image processing library
- ✅ **File Download** - serving files to users
- ✅ **Streaming Response** - streaming data delivery
- ✅ **Static Files** - serving static files
- ✅ **Path Operations** - file system operations

## 🚀 How to Run

```bash
# Install dependencies
pip install fastapi uvicorn pillow python-multipart

# Run server
cd example_04
python main.py
# or
uvicorn main:app --reload
```

Documentation: `http://localhost:8000/docs`

---

## 🖼️ Image Operations

### 1. Upload Image

```bash
# Upload via curl
curl -X POST "http://localhost:8000/upload/" \
  -H "Content-Type: multipart/form-data" \
  -F "file=@photo.jpg"

# Response:
{
  "filename": "photo.jpg",
  "size_bytes": 245678,
  "format": "JPEG",
  "width": 1920,
  "height": 1080
}
```

**Swagger UI:** Use `/docs` to test file upload interactively

### 2. Resize Image

```bash
curl -X POST "http://localhost:8000/process/resize/" \
  -H "Content-Type: application/json" \
  -d '{
    "filename": "photo.jpg",
    "width": 800,
    "height": 600
  }'

# Response:
{
  "message": "Image resized successfully",
  "output_file": "resized_800x600_photo.jpg",
  "download_url": "/download/resized_800x600_photo.jpg"
}
```

### 3. Convert Format

```bash
curl -X POST "http://localhost:8000/process/convert/" \
  -H "Content-Type: application/json" \
  -d '{
    "filename": "photo.jpg",
    "format": "PNG"
  }'

# Converts JPEG → PNG
```

### 4. Download Image

```bash
# Download as attachment
curl "http://localhost:8000/download/resized_800x600_photo.jpg" \
  --output image.jpg

# Or open in browser:
# http://localhost:8000/download/resized_800x600_photo.jpg
```

### 5. Preview Image

```bash
# Display in browser (inline, not download)
# http://localhost:8000/preview/resized_800x600_photo.jpg
```

### 6. Generate Thumbnail

```bash
# On-the-fly thumbnail (not saved to disk)
curl "http://localhost:8000/thumbnail/photo.jpg?size=150" \
  --output thumb.png
```

### 7. List Images

```bash
curl "http://localhost:8000/list/"

# Response:
{
  "uploaded": ["photo.jpg", "image.png"],
  "processed": ["resized_800x600_photo.jpg"]
}
```

---

## 📁 File Structure

```
example_04/
├── main.py          # FastAPI application
├── README.md        # This file
├── requirements.txt # Dependencies
├── uploads/         # Uploaded images (created automatically)
└── processed/       # Processed images (created automatically)
```

---

## 🔍 Key Concepts

### File Upload with Validation

```python
@app.post("/upload/")
async def upload_image(file: UploadFile = File(...)):
    # Validate file type
    if not file.content_type.startswith("image/"):
        raise HTTPException(400, "File must be an image")

    # Save file
    with open(f"uploads/{file.filename}", "wb") as buffer:
        shutil.copyfileobj(file.file, buffer)
```

**Important:**
- `UploadFile` - FastAPI type for file uploads
- `File(...)` - marks parameter as file upload
- Requires `python-multipart` package

### Image Processing with PIL

```python
from PIL import Image

# Open image
with Image.open("photo.jpg") as img:
    # Resize
    img.thumbnail((800, 600), Image.Resampling.LANCZOS)

    # Convert format
    img.save("output.png", format="PNG")

    # Get metadata
    width, height = img.size
    format = img.format
```

### File Response Types

**1. FileResponse** - for file downloads:
```python
return FileResponse(
    path="image.jpg",
    filename="download.jpg",  # Download name
    media_type="application/octet-stream"  # Force download
)
```

**2. StreamingResponse** - for streaming data:
```python
img_bytes = io.BytesIO()
img.save(img_bytes, format='PNG')
img_bytes.seek(0)

return StreamingResponse(img_bytes, media_type="image/png")
```

**3. Static Files** - for serving directories:
```python
app.mount("/static", StaticFiles(directory="processed"), name="static")
# Access: http://localhost:8000/static/image.jpg
```

### Path Operations

```python
from pathlib import Path

UPLOAD_DIR = Path("uploads")
UPLOAD_DIR.mkdir(exist_ok=True)  # Create if doesn't exist

file_path = UPLOAD_DIR / "photo.jpg"  # Join paths
file_path.exists()  # Check if exists
file_path.stat().st_size  # Get file size
```

---

## 🎯 Workflow Example

```bash
# 1. Upload image
curl -X POST "http://localhost:8000/upload/" -F "file=@cat.jpg"

# 2. Resize to 500x500
curl -X POST "http://localhost:8000/process/resize/" \
  -d '{"filename": "cat.jpg", "width": 500, "height": 500}'

# 3. Convert to PNG
curl -X POST "http://localhost:8000/process/convert/" \
  -d '{"filename": "cat.jpg", "format": "PNG"}'

# 4. Download processed image
curl "http://localhost:8000/download/cat.png" -o cat_processed.png

# 5. Get thumbnail
curl "http://localhost:8000/thumbnail/cat.jpg?size=100" -o thumb.png
```

---

## 📝 Practice Tasks

1. ✏️ Add image rotation (90°, 180°, 270°)
2. ✏️ Implement image filters (grayscale, blur, sharpen)
3. ✏️ Add watermark to images
4. ✏️ Create image gallery endpoint with HTML
5. ✏️ Implement image compression with quality settings
6. ✏️ Add bulk upload for multiple files
7. ✏️ Generate image thumbnails for gallery

---

## 🐛 Common Issues

### "python-multipart not installed"
```bash
pip install python-multipart
```

### "Pillow not installed"
```bash
pip install Pillow
```

### "Permission denied" when creating directories
- Check directory permissions
- Run with proper user rights

### "Image format not recognized"
- Ensure uploaded file is valid image
- Check file extension matches content

---

## 🔗 Next Steps

After completing this example, proceed to **Example 05: Dependency Injection**

**What's next:**
- Dependency Injection pattern
- Service Layer architecture
- Repository Pattern
- Advanced application structure

---

**Working with images is essential for many web applications! 🖼️**
