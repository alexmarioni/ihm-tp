import textwrap
from pathlib import Path

from PIL import Image, ImageDraw, ImageFont

FONTS_DIR = Path(__file__).parent.parent / "assets" / "fonts"


def _load_font(size: int) -> ImageFont.FreeTypeFont | ImageFont.ImageFont:
    candidates = [
        FONTS_DIR / "NotoSans-Bold.ttf",
        Path("C:/Windows/Fonts/arialbd.ttf"),
        Path("C:/Windows/Fonts/arial.ttf"),
        Path("C:/Windows/Fonts/calibrib.ttf"),
    ]
    for path in candidates:
        if path.exists():
            return ImageFont.truetype(str(path), size)
    return ImageFont.load_default()


def render_text_overlay(
    text: str,
    width: int = 1080,
    height: int = 1920,
    font_size: int = 88,
    position: str = "bottom_third",
    text_color: tuple = (255, 255, 255, 245),
    shadow_color: tuple = (0, 0, 0, 210),
) -> Image.Image:
    """Genera un PNG RGBA transparente con texto para usar como overlay en FFmpeg."""
    img = Image.new("RGBA", (width, height), (0, 0, 0, 0))
    draw = ImageDraw.Draw(img)
    font = _load_font(font_size)

    lines = textwrap.wrap(text, width=14)
    line_height = font_size + 14
    block_h = len(lines) * line_height

    if position == "bottom_third":
        y_start = int(height * 0.73)
    elif position == "top_third":
        y_start = int(height * 0.07)
    elif position == "center":
        y_start = (height - block_h) // 2
    else:
        y_start = int(height * 0.73)

    for i, line in enumerate(lines):
        bbox = draw.textbbox((0, 0), line, font=font)
        text_w = bbox[2] - bbox[0]
        x = (width - text_w) // 2
        y = y_start + i * line_height

        # Sombra difusa (4 desplazamientos)
        for dx, dy in [(-3, -3), (3, -3), (-3, 3), (3, 3), (0, 4)]:
            draw.text((x + dx, y + dy), line, font=font, fill=shadow_color)

        draw.text((x, y), line, font=font, fill=text_color)

    return img
