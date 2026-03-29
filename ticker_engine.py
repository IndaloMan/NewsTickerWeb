import os
from PIL import Image, ImageDraw, ImageFont

WINDOWS_FONTS = [
    'C:/Windows/Fonts/arialbd.ttf',
    'C:/Windows/Fonts/arial.ttf',
    'C:/Windows/Fonts/calibrib.ttf',
    'C:/Windows/Fonts/calibri.ttf',
    'C:/Windows/Fonts/verdanab.ttf',
    'C:/Windows/Fonts/verdana.ttf',
]


class TickerEngine:
    """Pre-renders the ticker strip and generates frames for a given time."""

    def __init__(self, config):
        self.config = config
        self._strip = None
        self._strip_width = 0
        self._logo_base = None
        self._logo_size = 0
        self._fixed_width = 0
        self._label_text = ''
        self._label_font = None
        self._label_w = 0
        self._right_logo = None
        self._right_logo_w = 0  # total reserved width including padding
        self._item_positions = []  # [{text, url, x, width}] for interactive timing

    def build(self):
        """Call once before rendering to pre-build strip and logos."""
        self._build_logo()
        self._build_right_logo()
        self._build_strip()
        self._fixed_width = (self._logo_size + 8 if self._logo_base else 0) + self._label_w

    def content_duration(self, frame_width=1920):
        """Return the time (seconds) for one complete pass including blank lead-in."""
        scroll_speed = self.config['style']['scroll_speed']
        if scroll_speed <= 0:
            return 0
        scrolling_width = max(frame_width - self._fixed_width - self._right_logo_w, 1)
        return (self._strip_width + scrolling_width) / scroll_speed

    def get_item_timings(self, frame_width=1920):
        """Return [{text, url, start, end}] timing for each ticker item."""
        scroll_speed = self.config['style']['scroll_speed']
        if scroll_speed <= 0:
            return []
        scrolling_width = max(frame_width - self._fixed_width - self._right_logo_w, 1)
        result = []
        for item in self._item_positions:
            t_start = item['x'] / scroll_speed
            t_end = (scrolling_width + item['x'] + item['width']) / scroll_speed
            result.append({
                'text': item['text'],
                'url': item['url'],
                'start': round(t_start, 2),
                'end': round(t_end, 2),
            })
        return result

    def get_frame(self, t, frame_width):
        """Return a PIL RGB Image of the ticker bar at time t (seconds)."""
        style = self.config['style']
        bar_height = style['bar_height']
        bar_color = style['bar_color']
        scroll_speed = style['scroll_speed']

        frame = Image.new('RGB', (frame_width, bar_height), bar_color)
        x_cursor = 0

        # --- Fixed: spinning logo ---
        if self._logo_base is not None:
            angle = (style['logo_spin_speed'] * t) % 360
            rotated = self._logo_base.rotate(-angle, resample=Image.BICUBIC, expand=False)
            y_pos = (bar_height - self._logo_size) // 2
            frame.paste(rotated, (x_cursor + 4, y_pos), rotated.split()[3])
            x_cursor += self._logo_size + 8

        # --- Fixed: LIVE/BREAKING label ---
        if self._label_text and self._label_font:
            draw = ImageDraw.Draw(frame)
            label_color = style['label_color']
            draw.text(
                (x_cursor + 10, bar_height // 2),
                self._label_text,
                font=self._label_font,
                fill=label_color,
                anchor='lm'
            )
            x_cursor += self._label_w

        # --- Scrolling text strip (leaves room for right logo) ---
        scrolling_width = frame_width - x_cursor - self._right_logo_w
        if scrolling_width > 0 and self._strip_width > 0:
            crop = Image.new('RGB', (scrolling_width, bar_height), bar_color)

            loop = self.config['output'].get('loop', False)
            offset = int(scroll_speed * t)

            if offset < scrolling_width:
                # Lead-in: blank bar, text enters from right edge
                visible = min(offset, self._strip_width)
                if visible > 0:
                    piece = self._strip.crop((0, 0, visible, bar_height))
                    crop.paste(piece, (scrolling_width - visible, 0))
            else:
                # Scroll phase
                pos = (offset - scrolling_width) % self._strip_width if loop else offset - scrolling_width
                x = 0
                while x < scrolling_width and pos < self._strip_width:
                    available = self._strip_width - pos
                    take = min(available, scrolling_width - x)
                    piece = self._strip.crop((pos, 0, pos + take, bar_height))
                    crop.paste(piece, (x, 0))
                    x += take
                    pos = (pos + take) % self._strip_width if loop else pos + take

            frame.paste(crop, (x_cursor, 0))

        # --- Fixed: right logo (static, natural shape, flush to right edge) ---
        if self._right_logo is not None:
            x_pos = frame_width - self._right_logo_w
            frame.paste(self._right_logo, (x_pos, 0), self._right_logo.split()[3])

        return frame

    # ------------------------------------------------------------------
    # Internal builders
    # ------------------------------------------------------------------

    def _build_logo(self):
        content = self.config['content']
        style = self.config['style']
        bar_height = style['bar_height']

        if not content['logo_enabled'] or not content['logo_path']:
            self._logo_base = None
            return

        path = content['logo_path']
        if not os.path.exists(path):
            self._logo_base = None
            return

        size = bar_height - 4
        img = Image.open(path).convert('RGBA')
        img = img.resize((size, size), Image.LANCZOS)

        mask = Image.new('L', (size, size), 0)
        draw = ImageDraw.Draw(mask)
        draw.ellipse([0, 0, size - 1, size - 1], fill=255)
        img.putalpha(mask)

        self._logo_base = img
        self._logo_size = size

    def _build_right_logo(self):
        content = self.config['content']
        style = self.config['style']
        bar_height = style['bar_height']

        if not content.get('right_logo_enabled') or not content.get('right_logo_path'):
            self._right_logo = None
            self._right_logo_w = 0
            return

        path = content['right_logo_path']
        if not os.path.exists(path):
            self._right_logo = None
            self._right_logo_w = 0
            return

        img = Image.open(path).convert('RGBA')
        orig_w, orig_h = img.size
        target_w = max(1, int(orig_w * bar_height / orig_h))
        img = img.resize((target_w, bar_height), Image.LANCZOS)

        self._right_logo = img
        self._right_logo_w = target_w  # no padding — flush to edges

    def _build_strip(self):
        content = self.config['content']
        style = self.config['style']
        bar_height = style['bar_height']
        font_size = style['font_size']
        bar_color = style['bar_color']
        text_color = style['text_color']
        sep_color = style['separator_color']

        font = self._load_font(font_size)
        label_font = self._load_font(font_size, bold=True)

        # Build fixed label info
        label = content['label']
        if label and label.strip():
            self._label_text = label
            self._label_font = label_font
            lw = self._text_width(label, label_font)
            self._label_w = lw + 24  # padding
        else:
            self._label_text = ''
            self._label_font = None
            self._label_w = 0

        # Build scrolling strip parts
        # Items support optional URL: "headline text | https://url"
        raw_items = [item.strip() for item in content['items'] if item.strip()]
        if not raw_items:
            raw_items = ['']

        items = []
        for raw in raw_items:
            if '|' in raw:
                text, url = raw.split('|', 1)
                items.append((text.strip(), url.strip()))
            else:
                items.append((raw, ''))

        separator = ' \u00a6 '
        loop = self.config['output'].get('loop', False)

        parts = []
        x_tracker = 0
        item_xs = []  # (text, url, x_start)
        for i, (text, url) in enumerate(items):
            item_xs.append((text, url, x_tracker))
            w = self._text_width(text, font)
            parts.append((text, text_color, font, w))
            x_tracker += w
            is_last = (i == len(items) - 1)
            if not is_last or loop:
                sep_w = self._text_width(separator, font)
                parts.append((separator, sep_color, font, sep_w))
                x_tracker += sep_w

        # Store item positions for interactive timing
        self._item_positions = [
            {'text': text, 'url': url, 'x': x, 'width': self._text_width(text, font)}
            for text, url, x in item_xs
        ]

        # Measure total strip width
        total_w = sum(w for _, _, _, w in parts)
        total_w = max(total_w, 100)

        # Render strip
        strip = Image.new('RGB', (total_w, bar_height), bar_color)
        draw = ImageDraw.Draw(strip)

        x = 0
        for text, color, f, w in parts:
            draw.text((x, bar_height // 2), text, font=f, fill=color, anchor='lm')
            x += w

        self._strip = strip
        self._strip_width = total_w

    def _text_width(self, text, font):
        bbox = font.getbbox(text)
        return bbox[2] - bbox[0]

    def _load_font(self, size, bold=False):
        # Try user-specified font first
        font_path = self.config['style']['font_path']
        if font_path and os.path.exists(font_path):
            try:
                return ImageFont.truetype(font_path, size)
            except Exception:
                pass

        # Try Windows system fonts
        candidates = WINDOWS_FONTS if not bold else WINDOWS_FONTS
        if bold:
            # Prefer bold variants
            bold_fonts = [f for f in WINDOWS_FONTS if 'b.ttf' in f or 'bd.ttf' in f]
            candidates = bold_fonts + [f for f in WINDOWS_FONTS if f not in bold_fonts]

        for fp in candidates:
            if os.path.exists(fp):
                try:
                    return ImageFont.truetype(fp, size)
                except Exception:
                    continue

        return ImageFont.load_default()
