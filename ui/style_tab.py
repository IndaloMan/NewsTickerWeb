import tkinter as tk
from tkinter import ttk, colorchooser, filedialog

import config_manager


class StyleTab:
    def __init__(self, notebook, config):
        self.config = config
        self._current_orientation = 'landscape'
        self.frame = ttk.Frame(notebook)
        notebook.add(self.frame, text='🎨  Style')
        self._build()

    def _build(self):
        pad = {'padx': 10, 'pady': 5}

        # --- Colours ---
        colour_frame = ttk.LabelFrame(self.frame, text='Colours')
        colour_frame.pack(fill='x', **pad)

        colour_defs = [
            ('bar_color',       'Bar background'),
            ('text_color',      'Ticker text'),
            ('separator_color', 'Separator  (¦)'),
            ('label_color',     'Label  (LIVE / BREAKING)'),
        ]
        self._colour_buttons = {}
        for key, label in colour_defs:
            row = ttk.Frame(colour_frame)
            row.pack(fill='x', padx=10, pady=4)
            ttk.Label(row, text=label, width=26, anchor='w').pack(side='left')
            btn = tk.Button(
                row,
                width=6,
                bg=self.config['style'][key],
                relief='solid',
                bd=1,
                cursor='hand2',
                command=lambda k=key: self._pick_colour(k)
            )
            btn.pack(side='left', padx=5)
            self._colour_buttons[key] = btn

        # --- Typography ---
        font_frame = ttk.LabelFrame(self.frame, text='Font')
        font_frame.pack(fill='x', **pad)

        font_row = ttk.Frame(font_frame)
        font_row.pack(fill='x', padx=10, pady=6)
        ttk.Label(font_row, text='Custom .ttf file:', width=16, anchor='w').pack(side='left')
        self.font_path_var = tk.StringVar(value=self.config['style']['font_path'])
        ttk.Entry(font_row, textvariable=self.font_path_var, width=40).pack(side='left', padx=(0, 5))
        ttk.Button(font_row, text='Browse…', command=self._browse_font).pack(side='left')
        ttk.Label(font_frame, text='(Leave blank to use system Arial)', foreground='gray').pack(
            anchor='w', padx=10, pady=(0, 6)
        )

        # --- Sliders ---
        slider_frame = ttk.LabelFrame(self.frame, text='Size & Speed')
        slider_frame.pack(fill='x', **pad)

        self._sliders = {}
        slider_defs = [
            ('font_size',       'Font size (px)',          16,  96,  1),
            ('bar_height',      'Bar height (px)',         40, 156,  1),
            ('scroll_speed',    'Scroll speed (px/sec)',   50, 500,  5),
            ('logo_spin_speed', 'Logo spin (deg/sec)',      0, 360,  5),
        ]
        for key, label, lo, hi, step in slider_defs:
            self._add_slider(slider_frame, key, label, lo, hi, step)

        self._save_sliders_btn = ttk.Button(
            slider_frame,
            text='Save sliders (landscape)',
            command=self._save_slider_presets
        )
        self._save_sliders_btn.pack(anchor='e', padx=10, pady=(2, 8))

        # --- Left Logo ---
        logo_frame = ttk.LabelFrame(self.frame, text='Left Logo (circular, spinning)')
        logo_frame.pack(fill='x', **pad)

        self.logo_enabled_var = tk.BooleanVar(value=self.config['content']['logo_enabled'])
        ttk.Checkbutton(
            logo_frame,
            text='Enable left logo',
            variable=self.logo_enabled_var,
            command=self._on_logo_toggle
        ).pack(anchor='w', padx=10, pady=(8, 2))

        path_row = ttk.Frame(logo_frame)
        path_row.pack(fill='x', padx=10, pady=(0, 8))

        self.logo_path_var = tk.StringVar(value=self.config['content']['logo_path'])
        self.logo_entry = ttk.Entry(path_row, textvariable=self.logo_path_var, width=50)
        self.logo_entry.pack(side='left', fill='x', expand=True, padx=(0, 5))
        self.logo_browse_btn = ttk.Button(path_row, text='Browse…', command=self._browse_logo)
        self.logo_browse_btn.pack(side='left')

        self._on_logo_toggle()

        # --- Right Logo ---
        rlogo_frame = ttk.LabelFrame(self.frame, text='Right Logo (natural shape, static)')
        rlogo_frame.pack(fill='x', **pad)

        self.right_logo_enabled_var = tk.BooleanVar(
            value=self.config['content'].get('right_logo_enabled', False)
        )
        ttk.Checkbutton(
            rlogo_frame,
            text='Enable right logo',
            variable=self.right_logo_enabled_var,
            command=self._on_right_logo_toggle
        ).pack(anchor='w', padx=10, pady=(8, 2))

        rpath_row = ttk.Frame(rlogo_frame)
        rpath_row.pack(fill='x', padx=10, pady=(0, 8))

        self.right_logo_path_var = tk.StringVar(
            value=self.config['content'].get('right_logo_path', '')
        )
        self.right_logo_entry = ttk.Entry(rpath_row, textvariable=self.right_logo_path_var, width=50)
        self.right_logo_entry.pack(side='left', fill='x', expand=True, padx=(0, 5))
        self.right_logo_browse_btn = ttk.Button(
            rpath_row, text='Browse…', command=self._browse_right_logo
        )
        self.right_logo_browse_btn.pack(side='left')

        self._on_right_logo_toggle()

    def _add_slider(self, parent, key, label, lo, hi, step):
        row = ttk.Frame(parent)
        row.pack(fill='x', padx=10, pady=4)
        ttk.Label(row, text=label, width=26, anchor='w').pack(side='left')

        val_var = tk.IntVar(value=self.config['style'][key])
        value_label = ttk.Label(row, textvariable=val_var, width=4, anchor='e')
        value_label.pack(side='right')

        slider = ttk.Scale(
            row,
            from_=lo,
            to=hi,
            orient='horizontal',
            variable=val_var,
            command=lambda v, vv=val_var: vv.set(round(float(v) / step) * step)
        )
        slider.pack(side='left', fill='x', expand=True, padx=5)
        self._sliders[key] = val_var

    def _on_logo_toggle(self):
        state = 'normal' if self.logo_enabled_var.get() else 'disabled'
        self.logo_entry.configure(state=state)
        self.logo_browse_btn.configure(state=state)

    def _on_right_logo_toggle(self):
        state = 'normal' if self.right_logo_enabled_var.get() else 'disabled'
        self.right_logo_entry.configure(state=state)
        self.right_logo_browse_btn.configure(state=state)

    def _browse_logo(self):
        path = filedialog.askopenfilename(
            title='Select Left Logo Image',
            filetypes=[('Image files', '*.png *.jpg *.jpeg *.bmp *.gif'), ('All files', '*.*')]
        )
        if path:
            self.logo_path_var.set(path)

    def _browse_right_logo(self):
        path = filedialog.askopenfilename(
            title='Select Right Logo Image',
            filetypes=[('Image files', '*.png *.jpg *.jpeg *.bmp *.gif'), ('All files', '*.*')]
        )
        if path:
            self.right_logo_path_var.set(path)

    def _pick_colour(self, key):
        current = self.config['style'][key]
        result = colorchooser.askcolor(color=current, title=f'Choose colour')
        if result and result[1]:
            hex_color = result[1]
            self.config['style'][key] = hex_color
            self._colour_buttons[key].configure(bg=hex_color)

    def _browse_font(self):
        path = filedialog.askopenfilename(
            title='Select Font File',
            filetypes=[('TrueType fonts', '*.ttf'), ('All files', '*.*')]
        )
        if path:
            self.font_path_var.set(path)

    def apply_orientation_presets(self, orientation):
        self._current_orientation = orientation
        self._save_sliders_btn.configure(text=f'Save sliders ({orientation})')
        presets = self.config.get(f'style_{orientation}', {})
        for key, var in self._sliders.items():
            if key in presets:
                var.set(presets[key])

    def _save_slider_presets(self):
        section = f'style_{self._current_orientation}'
        for key, var in self._sliders.items():
            self.config[section][key] = var.get()
        config_manager.save(self.config)

    def apply_to_config(self):
        self.config['style']['font_path'] = self.font_path_var.get()
        for key, var in self._sliders.items():
            self.config['style'][key] = var.get()
        # Colours are updated live in _pick_colour, but re-sync for safety
        for key, btn in self._colour_buttons.items():
            self.config['style'][key] = btn.cget('bg')
        self.config['content']['logo_path'] = self.logo_path_var.get()
        self.config['content']['logo_enabled'] = self.logo_enabled_var.get()
        self.config['content']['right_logo_path'] = self.right_logo_path_var.get()
        self.config['content']['right_logo_enabled'] = self.right_logo_enabled_var.get()
