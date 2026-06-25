#!/usr/bin/env python3
"""Субтитры в стиле «плашка» (как в видео мужчины 24_06): тёмная полупрозрачная
скруглённая подложка + белый жирный текст по центру + жёлтое активное слово.
Отличается от cut_reel «тень». Позиция — низ ~73%.

Рендерит прозрачную дорожку .mov с пословной подсветкой для наложения overlay.
Использование: импортируется build_subs_plashka(words, dur, out_png_dir).
"""
from PIL import Image, ImageDraw, ImageFont, ImageFilter

OUT_W, OUT_H = 1080, 1920
FONT = "assets/fonts/Unbounded.ttf"
SUB_CY = int(OUT_H * 0.74)        # центр блока субтитров (низ)
FONT_SIZE = 52
LINE_H = 76
MAX_LINE = 16                     # символов в строке
YELLOW = (255, 210, 63)
WHITE = (255, 255, 255)
PLATE = (38, 38, 40, 150)         # тёмная полупрозрачная подложка
PAD_X, PAD_Y = 38, 22
RADIUS = 28


def _font(size, weight=700):
    f = ImageFont.truetype(FONT, size)
    try: f.set_variation_by_axes([weight])
    except Exception: pass
    return f

F = _font(FONT_SIZE)


def wrap(words):
    lines, line = [], []
    for w in words:
        if line and len(" ".join(x["text"] for x in line + [w])) > MAX_LINE:
            lines.append(line); line = [w]
        else:
            line.append(w)
    if line: lines.append(line)
    return lines


def render_state(phrase, active_i, out_png):
    img = Image.new("RGBA", (OUT_W, OUT_H), (0, 0, 0, 0))
    d = ImageDraw.Draw(img)
    lines = wrap(phrase)
    n = len(lines)
    block_h = n * LINE_H
    y0 = SUB_CY - block_h // 2
    # габариты подложки = по самой широкой строке
    widths = [d.textlength(" ".join(w["text"] for w in ln), font=F) for ln in lines]
    plate_w = max(widths) + PAD_X * 2
    px0 = (OUT_W - plate_w) / 2
    py0 = y0 - PAD_Y
    py1 = y0 + block_h + PAD_Y - (LINE_H - FONT_SIZE)
    # подложка с прозрачностью
    plate = Image.new("RGBA", img.size, (0, 0, 0, 0))
    ImageDraw.Draw(plate).rounded_rectangle([px0, py0, px0 + plate_w, py1], RADIUS, fill=PLATE)
    img.alpha_composite(plate)
    # текст
    flat = 0
    for li, ln in enumerate(lines):
        text = " ".join(w["text"] for w in ln)
        tw = d.textlength(text, font=F)
        x = (OUT_W - tw) / 2
        y = y0 + li * LINE_H
        for w in ln:
            color = YELLOW if flat == active_i else WHITE
            d.text((x, y), w["text"], font=F, fill=color)
            x += d.textlength(w["text"] + " ", font=F)
            flat += 1
    img.save(out_png)
