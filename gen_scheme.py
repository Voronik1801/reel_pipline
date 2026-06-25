#!/usr/bin/env python3
"""Панель-схема в НИЖНЕЙ части кадра (под лицом) для обучающих рилсов.
Брендовый стиль: тёмно-зелёная вуаль + золотые цифры/рамки + кремовый текст,
заголовок Cormorant. Стрелки — фигурами (юникод-стрелки рендерятся квадратом).

Запуск: python3 gen_scheme.py <reel_id> <вход.mp4> <выход.mp4>
Накладывает панель в окне [APPEAR, до финала] с фейдом.
"""
import sys, subprocess, tempfile
from pathlib import Path
from PIL import Image, ImageDraw, ImageFont

W, H = 1080, 1920
UNB = "assets/fonts/Unbounded.ttf"; COR = "assets/fonts/CormorantGaramondItalic.ttf"
CREAM = (245, 240, 225); GOLD = (255, 210, 63); VEIL = (10, 22, 15, 210)
PANEL_Y0 = 1170          # верх панели (лицо выше — не перекрывается)
APPEAR, TAIL = 2.5, 3.5  # старт после обложки; хвост (финал) без панели

# Схемы по роликам: заголовок + шаги (номер крупно, подпись)
SCHEMES = {
    "premium1": {"title": "от нуля до профи", "steps": [
        "Контекст — дай ИИ свой",
        "4D-тест — что отдать",
        "Свой маленький скилл",
        "Харнес — обвязка модели",
        "Система — личная ОС",
    ]},
    "premium2": {"title": "3 способа начать", "steps": [
        "Сложи заметки в одну папку",
        "Claude + data governance",
        "Семантика = меньше токенов",
    ]},
    "etl": {"title": "данные — это база", "steps": [
        "Extract — собрать данные",
        "Transform — преобразовать",
        "Load — выгрузить (Telegram)",
    ]},
}


def font(path, size, weight=None):
    f = ImageFont.truetype(path, size)
    if weight:
        try: f.set_variation_by_axes([weight])
        except Exception: pass
    return f


def panel_png(rid, out):
    sch = SCHEMES[rid]; steps = sch["steps"]
    img = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    d = ImageDraw.Draw(img)
    pad = 40; x0 = pad; x1 = W - pad
    row_h = 104; head_h = 96
    y1 = PANEL_Y0 + head_h + len(steps) * row_h + 30
    # вуаль-подложка + золотая рамка
    d.rounded_rectangle([x0, PANEL_Y0, x1, y1], 34, fill=VEIL, outline=GOLD, width=3)
    # заголовок (Cormorant золото)
    ft = font(COR, 64)
    tw = d.textlength(sch["title"], font=ft)
    d.text(((W - tw) / 2, PANEL_Y0 + 16), sch["title"], font=ft, fill=GOLD)
    # шаги
    fnum = font(UNB, 46, 800); fstep = font(UNB, 38, 600)
    sy = PANEL_Y0 + head_h
    for i, s in enumerate(steps):
        cy = sy + i * row_h
        # золотой кружок с номером
        r = 34; cx = x0 + 56
        d.ellipse([cx - r, cy + 8, cx + r, cy + 8 + 2 * r], fill=GOLD)
        n = str(i + 1)
        nw = d.textlength(n, font=fnum)
        d.text((cx - nw / 2, cy + 12), n, font=fnum, fill=(10, 22, 15))
        # подпись (авто-уменьшение шрифта, чтобы влезть в рамку)
        tx = cx + r + 28; avail = x1 - tx - 24
        fs = fstep
        for sz in (38, 35, 32, 29):
            fs = font(UNB, sz, 600)
            if d.textlength(s, font=fs) <= avail: break
        d.text((tx, cy + 18), s, font=fs, fill=CREAM)
        # коннектор-линия между кружками (вместо юникод-стрелки)
        if i < len(steps) - 1:
            d.line([cx, cy + 8 + 2 * r, cx, cy + row_h + 8], fill=GOLD, width=4)
    img.save(out)


def main():
    rid, src, dst = sys.argv[1], sys.argv[2], sys.argv[3]
    tmp = Path(tempfile.mkdtemp(prefix="scheme_"))
    png = tmp / "panel.png"; panel_png(rid, png)
    # длительность -> панель до (конец - TAIL), фейд-ин/аут
    o = subprocess.run(["ffprobe", "-v", "error", "-show_entries", "format=duration",
                        "-of", "default=nw=1:nk=1", src], capture_output=True, text=True)
    dur = float(o.stdout.strip()); off = dur - TAIL
    subprocess.run(["ffmpeg", "-y", "-v", "error", "-i", src, "-loop", "1", "-t", str(dur), "-i", str(png),
        "-filter_complex",
        f"[1:v]format=rgba,fade=t=in:st={APPEAR}:d=0.4:alpha=1,fade=t=out:st={off-0.4}:d=0.4:alpha=1[p];"
        f"[0:v][p]overlay=0:0:enable='between(t,{APPEAR},{off})'[v]",
        "-map", "[v]", "-map", "0:a", "-c:v", "libx264", "-preset", "medium", "-crf", "19",
        "-pix_fmt", "yuv420p", "-color_primaries", "bt709", "-color_trc", "bt709",
        "-colorspace", "bt709", "-c:a", "copy", dst], check=True)
    print(f"OK схема {rid} -> {dst}")


if __name__ == "__main__":
    main()
