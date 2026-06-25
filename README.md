# 🎬 Reel Pipeline — переносимый тулкит

Монтаж вертикальных рилсов из съёмки на iPhone: цвет «как на айфоне», субтитры,
фирменный финал, обложка. Это **чистый переносимый набор** — без чужих видео и личных данных.

## Быстрый старт
```bash
bash pipeline_check.sh                 # проверить окружение
# 1) положи свою съёмку в raw/, маскоты в assets/stickers/
# 2) avconvert -p Preset1920x1080 -s raw/SHOT.MOV -o raw_sdr/SHOT.mov --replace
# 3) whisper transcripts/SHOT.wav ... --word_timestamps True
# 4) cp templates/build_TEMPLATE.py build_myshoot.py   (заполни SOURCES/REELS)
#    cp templates/make_reel_TEMPLATE.py make_reel_myshoot.py  (заполни FINALE)
# 5) python3 make_reel_myshoot.py myreel
```
Полная инструкция → **[PIPELINE.md](PIPELINE.md)**.

## Что входит
- **Документы:** `PIPELINE.md` (мастер-инструкция), `pipeline_check.sh`.
- **Движки** (не трогать): `cut_reel`, `stitch_reel`, `sub_plashka`, `gen_finale`,
  `gen_cover`, `gen_polish`, `gen_music`, `find_stutters`, `find_deadair`, `gen_lut`.
- **Шаблоны** (копировать под съёмку): `templates/build_TEMPLATE.py`, `templates/make_reel_TEMPLATE.py`.
- **Ассеты:** шрифты (Google Fonts). Маскоты — свои, см. `assets/stickers/README.md`.

## Что НЕ входит (личное, по дизайну)
Видео, транскрипты, планы, готовые рилсы, конкретные `build_<дата>.py`. `.gitignore`
блокирует их от случайного коммита. Папки `raw/ transcripts/ plan/ cut/` создаются при первом запуске.

## Требования
macOS (для `avconvert` — нативный HDR→SDR как на iPhone) · ffmpeg · openai-whisper · Pillow · numpy.
