"""Knowledge base for food additives (E-numbers): Vietnamese name + risk level.

Risk levels are canonical strings: "low" | "medium" | "high".
Used to (1) enrich additive rows that have no risk_level, and
(2) detect additives directly from an ingredients text (OCR / manual entry).
"""

from __future__ import annotations

import re

# e_number -> (Vietnamese name, risk level)
ADDITIVE_KB: dict[str, tuple[str, str]] = {
    # Flavour enhancers
    "E620": ("Axit glutamic", "medium"),
    "E621": ("Mì chính / bột ngọt (MSG)", "medium"),
    "E622": ("Mononatri glutamat kali", "medium"),
    "E627": ("Dinatri guanylat", "medium"),
    "E631": ("Dinatri inosinat", "medium"),
    "E635": ("Dinatri 5'-ribonucleotit", "medium"),
    # Preservatives - nitrites/nitrates (cured meat)
    "E249": ("Kali nitrit", "high"),
    "E250": ("Natri nitrit (muối diêm)", "high"),
    "E251": ("Natri nitrat", "high"),
    "E252": ("Kali nitrat", "high"),
    # Preservatives - benzoates
    "E210": ("Axit benzoic", "medium"),
    "E211": ("Natri benzoat", "medium"),
    "E212": ("Kali benzoat", "medium"),
    # Preservatives - sorbates
    "E200": ("Axit sorbic", "low"),
    "E202": ("Kali sorbat", "low"),
    # Preservatives - sulfites (allergen-relevant)
    "E220": ("Lưu huỳnh dioxit", "high"),
    "E221": ("Natri sulfit", "high"),
    "E223": ("Natri metabisulfit", "high"),
    "E224": ("Kali metabisulfit", "high"),
    # Antioxidants
    "E319": ("TBHQ", "medium"),
    "E320": ("BHA", "high"),
    "E321": ("BHT", "medium"),
    "E300": ("Vitamin C (axit ascorbic)", "low"),
    "E306": ("Tocopherol (vitamin E)", "low"),
    # Colours - azo/synthetic (higher concern)
    "E102": ("Tartrazine (vàng)", "high"),
    "E104": ("Vàng quinoline", "medium"),
    "E110": ("Vàng cam FCF", "high"),
    "E122": ("Carmoisine (đỏ)", "high"),
    "E124": ("Ponceau 4R (đỏ)", "high"),
    "E127": ("Erythrosine (đỏ)", "high"),
    "E129": ("Allura Red (đỏ)", "high"),
    "E131": ("Xanh patent", "medium"),
    "E133": ("Xanh rực rỡ FCF", "medium"),
    "E150A": ("Caramel", "low"),
    "E150D": ("Caramel sulfit amoni", "medium"),
    "E160A": ("Beta-caroten", "low"),
    "E160C": ("Chiết xuất ớt paprika", "low"),
    "E171": ("Titan dioxit (TiO2)", "high"),
    "E172": ("Oxit sắt", "low"),
    # Sweeteners
    "E950": ("Acesulfam K", "medium"),
    "E951": ("Aspartame", "medium"),
    "E952": ("Cyclamate", "medium"),
    "E954": ("Saccharin", "medium"),
    "E955": ("Sucralose", "low"),
    "E960": ("Stevia", "low"),
    # Emulsifiers / stabilizers / thickeners (mostly low)
    "E322": ("Lecithin", "low"),
    "E330": ("Axit citric", "low"),
    "E331": ("Natri citrat", "low"),
    "E407": ("Carrageenan", "medium"),
    "E412": ("Gôm guar", "low"),
    "E415": ("Gôm xanthan", "low"),
    "E440": ("Pectin", "low"),
    "E466": ("Carboxymethyl cellulose", "low"),
    "E471": ("Mono- và diglycerid", "low"),
    "E500": ("Natri bicacbonat", "low"),
    "E501": ("Kali cacbonat", "low"),
    "E503": ("Amoni cacbonat", "low"),
    "E509": ("Canxi clorua", "low"),
    # Modified starches (E14x family)
    "E1400": ("Tinh bột biến tính", "low"),
    "E1404": ("Tinh bột oxy hóa", "low"),
    "E1412": ("Distarch phosphat", "low"),
    "E1420": ("Tinh bột acetat", "low"),
    "E1422": ("Distarch adipat acetyl hóa", "low"),
    "E1442": ("Distarch phosphat hydroxypropyl", "low"),
}

# Common additive names (VN/EN) -> canonical E-number, for text detection
NAME_TO_ENUMBER: dict[str, str] = {
    "bột ngọt": "E621",
    "mì chính": "E621",
    "mi chinh": "E621",
    "bot ngot": "E621",
    "monosodium glutamate": "E621",
    "msg": "E621",
    "glutamat": "E621",
    "glutamate": "E621",
    "muối diêm": "E250",
    "muoi diem": "E250",
    "nitrit": "E250",
    "nitrite": "E250",
    "nitrat": "E251",
    "nitrate": "E251",
    "benzoat": "E211",
    "benzoate": "E211",
    "sorbat": "E202",
    "sorbate": "E202",
    "sulfit": "E220",
    "sulfite": "E220",
    "sulphite": "E220",
    "aspartame": "E951",
    "saccharin": "E954",
    "sucralose": "E955",
    "stevia": "E960",
    "carrageenan": "E407",
    "tbhq": "E319",
    "bha": "E320",
    "bht": "E321",
    "tartrazine": "E102",
    "lecithin": "E322",
    "titan dioxit": "E171",
    "titanium dioxide": "E171",
    "tinh bột biến tính": "E1400",
}

RISK_LABELS_VI = {"low": "Thấp", "medium": "Trung bình", "high": "Cao"}

_ENUMBER_RE = re.compile(r"\bE[\s\-]?(\d{3,4})([A-Za-z]?)\b", re.IGNORECASE)


def normalize_enumber(raw: str | None) -> str | None:
    """Normalize a raw E-number token to canonical form, e.g. 'e 621' -> 'E621'."""
    if not raw:
        return None
    m = re.search(r"(\d{3,4})([A-Za-z]?)", raw)
    if not m:
        return None
    return f"E{m.group(1)}{m.group(2).upper()}"


def get_additive_info(e_number: str | None) -> dict | None:
    """Return {'name', 'risk'} for an E-number, trying exact then base (letterless)."""
    canonical = normalize_enumber(e_number)
    if not canonical:
        return None
    if canonical in ADDITIVE_KB:
        name, risk = ADDITIVE_KB[canonical]
        return {"e_number": canonical, "name": name, "risk": risk}
    base = re.sub(r"[A-Z]$", "", canonical)
    if base in ADDITIVE_KB:
        name, risk = ADDITIVE_KB[base]
        return {"e_number": canonical, "name": name, "risk": risk}
    return {"e_number": canonical, "name": None, "risk": None}


def extract_additives_from_text(text: str | None) -> list[dict]:
    """Detect additives from free ingredients text (E-numbers + common names).

    Returns an ordered, de-duplicated list of {'e_number', 'name', 'risk'}.
    """
    if not text:
        return []
    found: dict[str, dict] = {}
    for match in _ENUMBER_RE.finditer(text):
        canonical = normalize_enumber(match.group(0))
        if canonical and canonical not in found:
            info = get_additive_info(canonical) or {"e_number": canonical, "name": None, "risk": None}
            found[canonical] = info

    lowered = text.lower()
    for keyword, enumber in NAME_TO_ENUMBER.items():
        if keyword in lowered and enumber not in found:
            found[enumber] = get_additive_info(enumber) or {"e_number": enumber, "name": None, "risk": None}

    return list(found.values())
