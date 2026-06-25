#!/usr/bin/env python3
"""Нарезка рилса из исходника + вшитые субтитры в стиле «тень».

Стиль зафиксирован 2026-06-12: Unbounded SemiBold, белый текст с мягкой тенью
(GaussianBlur), активное слово — жёлтый #FFD23F, позиция ~70% высоты кадра.

Использование:
  python3 cut_reel.py --src raw/A001.mov --json transcripts/A001.json \
      --start 73.4 --end 98.1 --out cut/01_120skillov.mp4
"""
import argparse, json, subprocess, tempfile
from pathlib import Path
from PIL import Image, ImageDraw, ImageFont, ImageFilter

FONT = Path(__file__).parent / "assets/fonts/Unbounded.ttf"
OUT_W, OUT_H = 1080, 1920
SUB_Y = int(OUT_H * 0.16)        # верх блока субтитров (перенесён наверх 23_06; было 0.70)
FONT_SIZE = 48
LINE_H = 72
MAX_LINE = 20                    # символов в строке
MAX_LINES = 2
GAP_BREAK = 0.7                  # пауза (сек), после которой начинается новая фраза
YELLOW = (255, 210, 63)


def load_words(json_path, start, end):
    data = json.loads(Path(json_path).read_text())
    words = []
    for seg in data["segments"]:
        for w in seg.get("words", []):
            if w["start"] >= start - 0.05 and w["end"] <= end + 0.05:
                words.append({"text": w["word"].strip(), "start": w["start"] - start, "end": w["end"] - start})
    return words


def group_phrases(words):
    """Бьём слова на фразы ≤2 строк по длине и паузам."""
    phrases, cur = [], []
    for w in words:
        candidate = cur + [w]
        text_len = len(" ".join(x["text"] for x in candidate))
        long_pause = cur and w["start"] - cur[-1]["end"] > GAP_BREAK
        if cur and (text_len > MAX_LINE * MAX_LINES or long_pause):
            phrases.append(cur)
            cur = [w]
        else:
            cur = candidate
    if cur:
        phrases.append(cur)
    return phrases


def wrap_lines(phrase):
    lines, line = [], []
    for w in phrase:
        if line and len(" ".join(x["text"] for x in line + [w])) > MAX_LINE:
            lines.append(line)
            line = [w]
        else:
            line.append(w)
    if line:
        lines.append(line)
    return lines


def make_font(size, weight):
    f = ImageFont.truetype(str(FONT), size)
    try:
        f.set_variation_by_axes([weight])
    except Exception:
        pass
    return f


F_SUB = make_font(FONT_SIZE, 600)


def render_state(phrase, active_i, out_png):
    """PNG 1080x1920 (RGBA): фраза с тенью, слово active_i — жёлтое."""
    img = Image.new("RGBA", (OUT_W, OUT_H), (0, 0, 0, 0))
    d = ImageDraw.Draw(img)
    lines = wrap_lines(phrase)
    # тень
    shadow = Image.new("L", img.size, 0)
    ds = ImageDraw.Draw(shadow)
    flat_idx = 0
    for li, line in enumerate(lines):
        text = " ".join(w["text"] for w in line)
        total = d.textlength(text, font=F_SUB)
        x = (OUT_W - total) / 2
        y = SUB_Y + li * LINE_H
        ds.text((x + 7, y + 9), text, font=F_SUB, fill=235)
    shadow = shadow.filter(ImageFilter.GaussianBlur(9))
    black = Image.new("RGBA", img.size, (0, 0, 0, 255))
    img.paste(black, (0, 0), shadow)
    # текст
    flat_idx = 0
    for li, line in enumerate(lines):
        text = " ".join(w["text"] for w in line)
        total = d.textlength(text, font=F_SUB)
        x = (OUT_W - total) / 2
        y = SUB_Y + li * LINE_H
        for w in line:
            color = YELLOW if flat_idx == active_i else (255, 255, 255)
            d.text((x, y), w["text"], font=F_SUB, fill=color)
            x += d.textlength(w["text"] + " ", font=F_SUB)
            flat_idx += 1
    img.save(out_png)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--src", required=True)
    ap.add_argument("--json", required=True)
    ap.add_argument("--start", type=float, required=True)
    ap.add_argument("--end", type=float, required=True)
    ap.add_argument("--out", required=True)
    args = ap.parse_args()

    words = load_words(args.json, args.start, args.end)
    if not words:
        raise SystemExit("В этом интервале нет слов — проверь таймкоды")
    phrases = group_phrases(words)

    tmp = Path(tempfile.mkdtemp(prefix="reel_"))
    overlays = []  # (png, start, end)
    for pi, phrase in enumerate(phrases):
        for wi, w in enumerate(phrase):
            png = tmp / f"p{pi:02d}_w{wi:02d}.png"
            render_state(phrase, wi, png)
            until = phrase[wi + 1]["start"] if wi + 1 < len(phrase) else phrase[-1]["end"] + 0.15
            overlays.append((png, w["start"], until))

    # ffmpeg: trim → scale/crop до 1080x1920 → цепочка overlay
    inputs = ["-ss", str(args.start), "-to", str(args.end), "-i", args.src]
    for png, _, _ in overlays:
        inputs += ["-i", str(png)]
    fc = [f"[0:v]scale={OUT_W}:{OUT_H}:force_original_aspect_ratio=increase,crop={OUT_W}:{OUT_H}[v0]"]
    prev = "v0"
    for i, (_, s, e) in enumerate(overlays):
        nxt = f"v{i+1}"
        fc.append(f"[{prev}][{i+1}:v]overlay=0:0:enable='between(t,{s:.3f},{e:.3f})'[{nxt}]")
        prev = nxt
    cmd = ["ffmpeg", "-y", "-v", "error"] + inputs + [
        "-filter_complex", ";".join(fc), "-map", f"[{prev}]", "-map", "0:a",
        "-c:v", "libx264", "-preset", "medium", "-crf", "19",
        "-c:a", "aac", "-b:a", "192k", "-movflags", "+faststart", args.out]
    subprocess.run(cmd, check=True)
    print(f"OK {args.out}: {len(phrases)} фраз, {len(overlays)} слов-состояний")


if __name__ == "__main__":
    main()
