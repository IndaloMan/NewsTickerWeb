# NewsTicker

A configurable news ticker overlay generator for MP4 videos, designed for use with Filmora 15.

Generates a scrolling news ticker bar burned onto the bottom of a source video, auto-matching its resolution and frame rate.

---

## Requirements

- Python 3.13+
- [Pillow](https://pillow.readthedocs.io/) — frame rendering
- [imageio-ffmpeg](https://github.com/imageio/imageio-ffmpeg) — bundles FFmpeg (no separate install needed)

Install dependencies:

```
pip install pillow imageio-ffmpeg
```

---

## Running

```
python main.py
```

Settings are auto-saved to `ticker_config.json` on close and on each render.

---

## Interface

The app has two tabs: **Content** and **Style**.

### Content tab

| Section | Description |
|---|---|
| Ticker Items | One news item per line. Items scroll right-to-left, separated by ¦ (separator omitted when only one item and loop is off) |
| Ticker Label | Fixed label on the left edge — type free text or use the LIVE / BREAKING shortcuts |
| Ticker Timing | Start and end times (seconds) to protect opening/closing titles. **Loop** — ticked: scrolls continuously for the full start→end window; unticked: plays once then hides |
| Source Video | The MP4/MOV/AVI/MKV file to burn the ticker onto |
| Output MP4 | Where to save the finished composite video |
| Progress / Log | Live progress bar and detailed FFmpeg log during render |
| Create News Ticker | Renders the composite. Exit saves config and closes |

### Style tab

| Section | Description |
|---|---|
| Colours | Bar background, ticker text, separator (¦), label (LIVE/BREAKING) — click to pick |
| Font | Optional custom .ttf file; falls back to system Arial |
| Size & Speed | Font size, bar height, scroll speed, logo spin speed. Sliders auto-update when a source video is selected based on its orientation (portrait/landscape). Use **Save sliders** to store the current values as the default for that orientation |
| Left Logo | PNG/JPG burned as a circular spinning disc on the left edge |
| Right Logo | PNG/JPG scaled to bar height, static, flush to the right edge |

---

## How it works

1. On render, the source video's resolution and FPS are auto-detected via ffprobe.
2. A ticker bar MP4 is rendered frame-by-frame using Pillow and piped to FFmpeg. The bar starts blank; text enters from the right and scrolls left.
3. With loop off, the ticker plays once and closes — duration is calculated automatically from text length and scroll speed. With loop on, the ticker fills the full start→end window.
4. FFmpeg overlays the ticker bar onto the bottom of the source video using a `filter_complex` overlay, active only between the configured start and end times.
5. Audio from the source video is copied unchanged.

---

## File structure

```
NewsTicker/
├── main.py                 — entry point, 2-tab Tkinter app
├── config_manager.py       — load/save ticker_config.json
├── ticker_engine.py        — Pillow frame renderer (scroll, logos, label)
├── video_renderer.py       — FFmpeg subprocess: detect, render, composite
├── ticker_config.json      — auto-created on first run
└── ui/
    ├── content_tab.py      — Content tab (items, label, timing, paths, render)
    └── style_tab.py        — Style tab (colours, font, sizes, logos)
```

---

## Configuration

All settings are stored in `ticker_config.json` and loaded automatically on startup. Delete the file to reset to defaults.

Key settings:

| Key | Description |
|---|---|
| `content.items` | List of ticker text items |
| `content.label` | Fixed left label text (blank = none) |
| `content.logo_path` | Path to left logo image |
| `content.right_logo_path` | Path to right logo image |
| `style.bar_color` | Bar background hex colour |
| `style.bar_height` | Bar height in pixels |
| `style.scroll_speed` | Scroll speed in pixels/second |
| `output.start_time` | Ticker start time in seconds |
| `output.end_time` | Ticker end time in seconds |
| `output.source_video_path` | Source video to composite onto |
| `output.composite_path` | Output file path |
| `style_landscape.font_size` | Saved font size preset for landscape video |
| `style_landscape.bar_height` | Saved bar height preset for landscape video |
| `style_portrait.font_size` | Saved font size preset for portrait video |
| `style_portrait.bar_height` | Saved bar height preset for portrait video |
