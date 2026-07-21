from fastapi import APIRouter, File, HTTPException, UploadFile

from app.schemas.product import OcrIngredientsOut
from app.services.ingredients_ocr import extract_ingredients_text

router = APIRouter(prefix="/ocr", tags=["ocr"])


@router.post("/ingredients", response_model=OcrIngredientsOut)
async def ocr_ingredients(image: UploadFile = File(...)):
    if not image.content_type or not image.content_type.startswith("image/"):
        raise HTTPException(status_code=400, detail="File upload phải là ảnh")

    image_bytes = await image.read()
    if len(image_bytes) > 10 * 1024 * 1024:
        raise HTTPException(status_code=400, detail="Ảnh quá lớn (tối đa 10MB)")

    result = extract_ingredients_text(image_bytes)
    return OcrIngredientsOut(**result)
