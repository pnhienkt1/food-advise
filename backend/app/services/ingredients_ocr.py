from __future__ import annotations

import re
from io import BytesIO

import numpy as np
from PIL import Image, ImageFilter, ImageOps

try:
    import pytesseract
except Exception:  # pragma: no cover - optional dependency guard
    pytesseract = None


def preprocess_image(image_bytes: bytes) -> Image.Image:
    image = Image.open(BytesIO(image_bytes)).convert("RGB")
    gray = ImageOps.grayscale(image)
    denoised = gray.filter(ImageFilter.MedianFilter(size=3))
    boosted = ImageOps.autocontrast(denoised)
    arr = np.array(boosted)
    threshold = (arr > 160).astype(np.uint8) * 255
    out = Image.fromarray(threshold)
    if out.width < 1200:
        ratio = 1200 / out.width
        out = out.resize((1200, int(out.height * ratio)))
    return out


def parse_ingredients(raw_text: str) -> list[str]:
    compact = re.sub(r"\s+", " ", raw_text).strip()
    if not compact:
        return []
    cleaned = re.sub(r"(?i)^.*?(ingredients|thành phần)\s*[:\-]", "", compact).strip()
    parts = re.split(r"[,;]", cleaned)
    out = []
    for part in parts:
        token = part.strip(" .:-")
        if len(token) >= 2:
            out.append(token)
    return out[:120]


def extract_ingredients_text(image_bytes: bytes) -> dict:
    if pytesseract is None:
        return {
            "raw_text": "",
            "ingredients": [],
            "confidence": None,
            "notes": "pytesseract chưa được cài trong môi trường backend",
        }

    processed = preprocess_image(image_bytes)
    custom_config = "--oem 3 --psm 6"
    raw_text = pytesseract.image_to_string(processed, lang="vie+eng", config=custom_config)
    ingredients = parse_ingredients(raw_text)
    notes = "OCR local bằng pytesseract + tiền xử lý grayscale/threshold/denoise/resize"
    return {
        "raw_text": raw_text.strip(),
        "ingredients": ingredients,
        "confidence": None,
        "notes": notes,
    }
