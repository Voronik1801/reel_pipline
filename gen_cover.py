#!/usr/bin/env python3
"""Хук-обложка (стиль B) поверх первых ~2с рилса: вуаль + 2 строки
(кремовый Unbounded + золотой Cormorant) + искорки + стикер-маскот под акцентом.
Уходит фейдом на 2с — дальше живой кадр.

Запуск: python3 gen_cover.py <reel_id> <вход.mp4> <выход.mp4>
"""
import sys, subprocess, math, random, tempfile
from pathlib import Path
from PIL import Image, ImageDraw, ImageFont, ImageFilter

W, H = 1080, 1920
UNB = "assets/fonts/Unbounded.ttf"; COR = "assets/fonts/CormorantGaramondItalic.ttf"
CREAM = (245, 240, 225); GOLD = (255, 210, 63)
DUR, FADE = 2.2, 0.4   # длительность обложки и фейд-аут

# текст + акцент (золото, Cormorant) + стикер-маскот под акцентом
COVER = {
    "5":  {"l1": "3 способа освоить ИИ",     "l2": "за 1 день",       "st": "star"},
    "14": {"l1": "Data Governance",          "l2": "на даче",         "st": "duck"},
    "13": {"l1": "Обсидиан — это",           "l2": "читалка",         "st": "moon"},
    "1":  {"l1": "Что ждать, когда ждёшь",   "l2": "B2B SaaS",        "st": "strawberry-baby"},
    "2":  {"l1": "Золотое время",            "l2": "для креативных?", "st": "star"},
    "4":  {"l1": "Вам не нужен",             "l2": "второй мозг",     "st": "frog-fairy"},
    # 23_06
    "3k":       {"l1": "+3000 подписчиков",   "l2": "за 4 дня",          "st": "strawberry-baby"},
    "zaebalo":  {"l1": "Рубрика",             "l2": "ЗАЕБАЛО",           "st": "frog-fairy"},
    "premium1": {"l1": "Инстаграм Премиум",   "l2": "от 0 до профи",     "st": "star"},
    "premium2": {"l1": "3 способа начать",    "l2": "с ИИ",              "st": "phone1"},
    "psycho":   {"l1": "ИИ-эксперты",         "l2": "из тарологов",      "st": "moon"},
    "vagon":    {"l1": "Ты не опоздал",       "l2": "в ИИ",              "st": "star"},
    "fora":     {"l1": "Фора в ИИ —",         "l2": "полтора года",      "st": "frog-fairy"},
    "gonka":    {"l1": "Гонка нейросетей",    "l2": "не нужна",          "st": "phone2"},
    "product":  {"l1": "FOMO — это",          "l2": "продукт",           "st": "moon"},
    "etl":      {"l1": "База для ИИ —",       "l2": "это данные",        "st": "duck"},
    "voda":     {"l1": "Продают воду",        "l2": "как воздух",        "st": "star"},
    "dud":      {"l1": "Юра Дудь,",           "l2": "напиши мне",        "st": "phone1"},
}


def run(c): subprocess.run(c, check=True)


def fit(path, text, target, maxw=W - 110):
    s = target; f = ImageFont.truetype(path, s)
    d = ImageDraw.Draw(Image.new("RGBA", (4, 4)))
    while d.textlength(text, font=f) > maxw and s > 40:
        s -= 4; f = ImageFont.truetype(path, s)
    return f, s


def shadow(im, t, f, cx, y, fill, off=(5, 8), blur=14, sa=200):
    d = ImageDraw.Draw(im); w = d.textlength(t, font=f); x = cx - w / 2
    s = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    ImageDraw.Draw(s).text((x + off[0], y + off[1]), t, font=f, fill=(0, 0, 0, sa))
    im.alpha_composite(s.filter(ImageFilter.GaussianBlur(blur)))
    ImageDraw.Draw(im).text((x, y), t, font=f, fill=fill)
    return x, w


def stars(im, seed, cy, n=12, spread=360):
    rnd = random.Random(seed); d = ImageDraw.Draw(im)
    for i in range(n):
        a = rnd.uniform(0, 6.28); r = rnd.uniform(0.4, 1) * spread
        x = W / 2 + math.cos(a) * r; y = cy + math.sin(a) * r * 0.5; s = rnd.uniform(5, 12)
        c = (GOLD if i % 2 else CREAM) + (rnd.randint(120, 210),)
        d.polygon([(x, y-s), (x+s*0.3, y-s*0.3), (x+s, y), (x+s*0.3, y+s*0.3),
                   (x, y+s), (x-s*0.3, y+s*0.3), (x-s, y), (x-s*0.3, y-s*0.3)], fill=c)


def overlay_png(rid, path):
    c = COVER[rid]
    ov = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    ov.alpha_composite(Image.new("RGBA", (W, H), (10, 22, 15, 105)))   # вуаль (только на обложке 0–2с)
    Y1 = 760                        # по центру кадра (название видео)
    stars(ov, hash(rid) & 255, Y1 + 120)
    f1, s1 = fit(UNB, c["l1"], 72)
    try: f1.set_variation_by_axes([800])
    except Exception: pass
    shadow(ov, c["l1"], f1, W // 2, Y1, CREAM)
    Y2 = Y1 + int(s1 * 0.67)                                            # плотный межстрочный
    f2, s2 = fit(COR, c["l2"], 150)
    x2, w2 = shadow(ov, c["l2"], f2, W // 2, Y2, GOLD, off=(5, 8), blur=16)
    st = Image.open(f"assets/stickers/{c['st']}.png").convert("RGBA")
    fh = 200; fw = int(st.width * fh / st.height); st = st.resize((fw, fh))
    ov.alpha_composite(st, (int(x2 - fw * 0.15), Y2 + s2 - 40))
    ov.save(path)


def main():
    rid, src, dst = sys.argv[1], sys.argv[2], sys.argv[3]
    tmp = Path(tempfile.mkdtemp(prefix="cover_"))
    png = tmp / "cover.png"
    overlay_png(rid, png)
    run(["ffmpeg", "-y", "-v", "error", "-i", src, "-loop", "1", "-t", str(DUR), "-i", str(png),
         "-filter_complex",
         f"[1:v]format=rgba,fade=t=out:st={DUR-FADE}:d={FADE}:alpha=1[ov];"
         f"[0:v][ov]overlay=0:0:enable='lte(t,{DUR})'[v]",
         "-map", "[v]", "-map", "0:a",
         "-c:v", "libx264", "-preset", "medium", "-crf", "19", "-pix_fmt", "yuv420p",
         "-c:a", "copy", dst])
    print(f"OK обложка -> {dst}")


if __name__ == "__main__":
    main()
