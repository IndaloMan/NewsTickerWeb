# NewsTickerWeb

A configurable news ticker overlay generator for MP4 videos, with browser-based tools for creating and playing back interactive ticker overlays.

**GitHub Pages:** https://indaloman.github.io/NewsTickerWeb/

---

## Components

### Python desktop app
Renders a scrolling news ticker bar burned onto the bottom of a source video.

- `main.py` — entry point, Tkinter UI
- `ticker_engine.py` — Pillow frame renderer (scroll, logos, label)
- `video_renderer.py` — FFmpeg subprocess (detect, render, composite). Auto-writes a `-J.json` timing file alongside the output video.
- `config_manager.py` — loads/saves `ticker_config.json`
- `ui/content_tab.py` — Content tab (items, label, timing, paths, render)
- `ui/style_tab.py` — Style tab (colours, font, sizes, logos)

### editor.html
Browser tool for creating and editing JSON timing files.

- Load a video → JSON file picker opens automatically
- Add, edit, or delete ticker items (text, URL, start/end times)
- "Use current" buttons capture video playback position as timestamps
- Export downloads a named JSON file (`videoname-J.json`)
- Load an existing JSON to edit it

### player.html
Browser tool for playing a video with an interactive ticker overlay.

- Load a video → JSON file picker opens automatically
- Ticker items highlight in sync with video playback
- Active item shown as a clickable link above the player
- Links open in a reused popup window (1024×768), video pauses on click
- All items listed below with timestamps and links

---

## File naming convention

| File | Pattern |
|---|---|
| Rendered video | `YYYYMMDD - Name-N.mp4` |
| JSON timing file | `YYYYMMDD - Name-J.json` |

---

## JSON timing format

```json
[
  { "text": "Headline text", "url": "https://example.com", "start": 7.9, "end": 11.2 },
  { "text": "Another item",  "url": "",                    "start": 13.8, "end": 19.8 }
]
```

---

## Python app requirements

- Python 3.13+
- [Pillow](https://pillow.readthedocs.io/) — frame rendering
- [imageio-ffmpeg](https://github.com/imageio/imageio-ffmpeg) — bundles FFmpeg

```
pip install pillow imageio-ffmpeg
```

Run with:
```
python main.py
```

---

## Production use (Option A)

For public viewers, host the video and its `-J.json` file on a web server. The player can fetch the JSON automatically from a predictable URL alongside the video — no file picker needed. Videos are too large for GitHub; host them externally (CDN, Google Drive, own server).

---

## Configuration

Settings auto-save to `ticker_config.json` on close and on each render.

| Key | Description |
|---|---|
| `content.items` | List of ticker text items (supports `text \| https://url` format) |
| `content.label` | Fixed left label (LIVE / BREAKING / custom / blank) |
| `style.bar_color` | Bar background hex colour |
| `style.bar_height` | Bar height in pixels |
| `style.scroll_speed` | Scroll speed in pixels/second |
| `output.start_time` | Ticker start time in seconds |
| `output.end_time` | Ticker end time in seconds |
| `output.source_video_path` | Source video to composite onto |
| `output.composite_path` | Output file path |
