"""Font discovery and loading utilities with platform fallbacks."""

from pathlib import Path
from typing import Dict, List, Optional, Tuple
from PIL import ImageFont

# Well-known system font directories across operating systems
SYSTEM_FONT_DIRS = [
    Path("/System/Library/Fonts"),
    Path("/System/Library/Fonts/Supplemental"),
    Path("/Library/Fonts"),
    Path("/usr/share/fonts"),
    Path("/usr/local/share/fonts"),
    Path("C:/Windows/Fonts"),
]

# Cache loaded fonts to avoid repeated disk reads
_FONT_CACHE: Dict[Tuple[str, int], ImageFont.FreeTypeFont] = {}


def _find_font_file(name: str) -> Optional[Path]:
    """Search for a font by filename or family name in system directories."""
    # If it's already a full path
    direct_path = Path(name)
    if direct_path.is_file():
        return direct_path

    # Try common extensions
    variations = [name]
    if not name.lower().endswith((".ttf", ".ttc", ".otf")):
        variations.extend([f"{name}.ttf", f"{name}.ttc", f"{name}.otf"])

    for font_dir in SYSTEM_FONT_DIRS:
        if not font_dir.is_dir():
            continue
        for candidate in variations:
            target = font_dir / candidate
            if target.is_file():
                return target
            # Case-insensitive match within the folder
            for entry in font_dir.iterdir():
                if entry.name.lower() == candidate.lower() and entry.is_file():
                    return entry

    return None


def get_font(family_candidates: List[str], size: int) -> ImageFont.ImageFont:
    """Attempt to load the first available font from family_candidates,

    falling back to PIL's default scalable font if none found.
    """
    cache_key = ("::".join(family_candidates), size)
    if cache_key in _FONT_CACHE:
        return _FONT_CACHE[cache_key]

    for candidate in family_candidates:
        font_path = _find_font_file(candidate)
        if font_path:
            try:
                font = ImageFont.truetype(str(font_path), size=size)
                _FONT_CACHE[cache_key] = font
                return font
            except Exception:
                continue

    # Final fallback to Pillow default font (scalable in Pillow >= 10.0)
    try:
        font = ImageFont.load_default(size=size)
    except TypeError:
        # Fallback for very old Pillow
        font = ImageFont.load_default()

    _FONT_CACHE[cache_key] = font
    return font
