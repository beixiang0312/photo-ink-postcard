#!/usr/bin/env python3
import argparse
from pathlib import Path
from PIL import Image, ImageDraw, ImageFont, ImageStat

W, H, PHOTO_H = 1536, 2048, 1024
DEFAULT_IVORY = (244, 240, 229)
INK, SUB_INK = (52, 49, 43), (91, 87, 79)
TITLE_MAX_WIDTH = 1250


def contain(im: Image.Image, size: tuple[int, int]) -> Image.Image:
    target = Image.new("RGB", size, DEFAULT_IVORY)
    work = im.convert("RGB")
    work.thumbnail(size, Image.Resampling.LANCZOS)
    target.paste(work, ((size[0] - work.width) // 2, (size[1] - work.height) // 2))
    return target


def paper_color(im: Image.Image) -> tuple[int, int, int]:
    w, h = im.size
    boxes = [(0, 0, 96, 96), (w - 96, 0, w, 96), (0, h - 72, 96, h), (w - 96, h - 72, w, h)]
    means = [ImageStat.Stat(im.crop(box)).mean[:3] for box in boxes]
    return tuple(round(sum(m[i] for m in means) / len(means)) for i in range(3))


def edge_mask(size: tuple[int, int], feather: int = 52) -> Image.Image:
    w, h = size
    mask = Image.new("L", size, 255)
    px = mask.load()
    for y in range(h):
        bottom = 255 if y < h - feather else round(255 * max(0, h - 1 - y) / feather)
        for x in range(w):
            side = min(x, w - 1 - x)
            px[x, y] = min(255 if side >= feather else round(255 * side / feather), bottom)
    return mask


def has_cjk(text: str) -> bool:
    return any(
        "\u3400" <= ch <= "\u4dbf"
        or "\u4e00" <= ch <= "\u9fff"
        or "\uf900" <= ch <= "\ufaff"
        for ch in text
    )


def title_font_path(text: str) -> Path:
    candidates = (
        [Path(r"C:\Windows\Fonts\NotoSerifSC-VF.ttf"), Path(r"C:\Windows\Fonts\simsun.ttc")]
        if has_cjk(text)
        else [Path(r"C:\Windows\Fonts\georgiai.ttf"), Path(r"C:\Windows\Fonts\BASKVILL.TTF")]
    )
    for path in candidates:
        if path.exists():
            return path
    raise SystemExit("找不到可用于主标题的字体。")


def fitted_font(draw: ImageDraw.ImageDraw, text: str, path: Path, start: int = 57, minimum: int = 34) -> ImageFont.FreeTypeFont:
    for size in range(start, minimum - 1, -1):
        font = ImageFont.truetype(str(path), size)
        bbox = draw.textbbox((0, 0), text, font=font)
        if bbox[2] - bbox[0] <= TITLE_MAX_WIDTH:
            return font
    raise SystemExit("主标题过长，无法在安全宽度内完整排版。")


def tracked_text(draw, text, font, center_x, y, fill, tracking=1):
    widths = [draw.textlength(ch, font=font) for ch in text]
    x = center_x - (sum(widths) + tracking * max(0, len(text) - 1)) / 2
    for ch, width in zip(text, widths):
        draw.text((round(x), y), ch, font=font, fill=fill)
        x += width + tracking


def main() -> None:
    parser = argparse.ArgumentParser(description="确定性合成一张 3:4 摄影水墨明信片。")
    parser.add_argument("--photo", required=True, help="上半区原始照片。")
    parser.add_argument("--panel", required=True, help="生成的下半区水墨底图。")
    parser.add_argument("--title", required=True, help="主标题精确文字，必须由用户或任务明确提供。")
    parser.add_argument("--subtitle", required=True, help="从本地短句库选定的英文次标题。")
    parser.add_argument("--out", required=True, help="新建的 PNG 输出路径。")
    args = parser.parse_args()

    title = args.title.strip()
    subtitle = args.subtitle.strip()
    if not title:
        raise SystemExit("主标题不能为空。请通过 --title 传入精确文字。")
    if not subtitle:
        raise SystemExit("次标题不能为空。")
    if any(ch in title + subtitle for ch in "{}[]"):
        raise SystemExit("标题中包含未替换的占位符字符。")

    with Image.open(args.photo) as im:
        upper = contain(im, (W, PHOTO_H))
    with Image.open(args.panel) as im:
        original = im.convert("RGB")
        bg = paper_color(original)
        panel = original.crop((0, 40, original.width, min(original.height, 970)))
    target_w = 1300
    panel = panel.resize((target_w, round(panel.height * target_w / panel.width)), Image.Resampling.LANCZOS)
    card = Image.new("RGB", (W, H), bg)
    card.paste(upper, (0, 0))
    card.paste(panel, ((W - panel.width) // 2, 1042), edge_mask(panel.size))

    sub_path = Path(r"C:\Windows\Fonts\calibril.ttf")
    if not sub_path.exists():
        raise SystemExit("找不到次标题字体。")
    draw = ImageDraw.Draw(card)
    title_font = fitted_font(draw, title, title_font_path(title))
    sub_font = ImageFont.truetype(str(sub_path), 31)
    bbox = draw.textbbox((0, 0), title, font=title_font)
    draw.text(((W - (bbox[2] - bbox[0])) // 2, 1830), title, font=title_font, fill=INK)
    tracked_text(draw, subtitle, sub_font, W // 2, 1921, SUB_INK)

    out = Path(args.out)
    out.parent.mkdir(parents=True, exist_ok=True)
    card.save(out, "PNG", optimize=True)
    print(out.resolve())


if __name__ == "__main__":
    main()
