import tkinter as tk
from tkinter import ttk, filedialog
import threading
import queue

from ticker_engine import TickerEngine
import video_renderer


class ContentTab:
    def __init__(self, notebook, config, get_config_fn, on_orientation_detected=None):
        self.config = config
        self.get_config = get_config_fn
        self._on_orientation_detected = on_orientation_detected
        self._q = queue.Queue()
        self.frame = ttk.Frame(notebook)
        notebook.add(self.frame, text='📝  Content')
        self._build()

    def _build(self):
        pad = {'padx': 10, 'pady': 5}

        # --- Ticker Items ---
        items_frame = ttk.LabelFrame(self.frame, text='Ticker Items (one per line)')
        items_frame.pack(fill='x', **pad)

        self.items_text = tk.Text(items_frame, height=5, wrap='word', font=('Consolas', 10))
        scroll = ttk.Scrollbar(items_frame, command=self.items_text.yview)
        self.items_text.configure(yscrollcommand=scroll.set)
        self.items_text.pack(side='left', fill='x', expand=False, padx=5, pady=5)
        scroll.pack(side='right', fill='y', pady=5)

        sep_info = ttk.Label(items_frame, text='Items separated by  ¦  |  To add a clickable link:  Headline text | https://example.com', foreground='gray')
        sep_info.pack(anchor='w', padx=5, pady=(0, 5))

        # --- Ticker Label ---
        label_frame = ttk.LabelFrame(self.frame, text='Ticker Label')
        label_frame.pack(fill='x', **pad)

        label_row = ttk.Frame(label_frame)
        label_row.pack(fill='x', padx=10, pady=8)

        ttk.Label(label_row, text='Label text:', anchor='w').pack(side='left')

        # Treat "NONE" from old configs as blank
        saved_label = self.config['content']['label']
        if saved_label == 'NONE':
            saved_label = ''
        self.label_var = tk.StringVar(value=saved_label)
        ttk.Entry(label_row, textvariable=self.label_var, width=20).pack(side='left', padx=(6, 12))

        ttk.Button(label_row, text='LIVE',     width=7,
                   command=lambda: self.label_var.set('LIVE')).pack(side='left', padx=2)
        ttk.Button(label_row, text='BREAKING', width=9,
                   command=lambda: self.label_var.set('BREAKING')).pack(side='left', padx=2)
        ttk.Button(label_row, text='Clear',    width=6,
                   command=lambda: self.label_var.set('')).pack(side='left', padx=(8, 0))

        ttk.Label(label_frame, text='Leave blank for no label.', foreground='gray').pack(
            anchor='w', padx=10, pady=(0, 6)
        )

        # --- Ticker Timing ---
        timing_frame = ttk.LabelFrame(self.frame, text='Ticker Timing (seconds)')
        timing_frame.pack(fill='x', **pad)

        time_row = ttk.Frame(timing_frame)
        time_row.pack(fill='x', padx=10, pady=6)

        ttk.Label(time_row, text='Start time:', anchor='w').pack(side='left')
        self.start_var = tk.DoubleVar(value=self.config['output']['start_time'])
        ttk.Spinbox(time_row, textvariable=self.start_var, from_=0, to=9999,
                    increment=1, width=7, format='%.1f').pack(side='left', padx=(4, 20))

        ttk.Label(time_row, text='End time:', anchor='w').pack(side='left')
        self.end_var = tk.DoubleVar(value=self.config['output']['end_time'])
        ttk.Spinbox(time_row, textvariable=self.end_var, from_=1, to=9999,
                    increment=1, width=7, format='%.1f').pack(side='left', padx=4)

        self.loop_var = tk.BooleanVar(value=self.config['output']['loop'])
        ttk.Checkbutton(
            timing_frame,
            text='Loop ticker content to fill the start→end window',
            variable=self.loop_var
        ).pack(anchor='w', padx=10, pady=(0, 4))
        ttk.Label(timing_frame,
                  text='Tip: set start/end to avoid overwriting opening and closing titles.',
                  foreground='gray').pack(anchor='w', padx=10, pady=(0, 6))

        # --- Video Details ---
        source_frame = ttk.LabelFrame(self.frame, text='Video Details')
        source_frame.pack(fill='x', **pad)

        loc_row = ttk.Frame(source_frame)
        loc_row.pack(fill='x', padx=10, pady=5)
        ttk.Label(loc_row, text='Location:', width=16, anchor='w').pack(side='left')
        self.location_var = tk.StringVar(value=self.config['output']['location'])
        ttk.Entry(loc_row, textvariable=self.location_var, width=46).pack(
            side='left', fill='x', expand=True, padx=(0, 5))
        ttk.Button(loc_row, text='Browse…', command=self._browse_location).pack(side='left')

        import os
        src_row = ttk.Frame(source_frame)
        src_row.pack(fill='x', padx=10, pady=5)
        ttk.Label(src_row, text='Source video:', width=16, anchor='w').pack(side='left')
        self._source_video_path_var = tk.StringVar(value=self.config['output']['source_video_path'])
        self.source_display_var = tk.StringVar(
            value=os.path.basename(self.config['output']['source_video_path']))
        ttk.Entry(src_row, textvariable=self.source_display_var, state='readonly').pack(
            side='left', fill='x', expand=True, padx=(0, 5))
        ttk.Button(src_row, text='Browse…', command=self._browse_source_video).pack(side='left')

        out_row = ttk.Frame(source_frame)
        out_row.pack(fill='x', padx=10, pady=(0, 5))
        ttk.Label(out_row, text='Output video:', width=16, anchor='w').pack(side='left')
        self._composite_path_var = tk.StringVar(value=self.config['output']['composite_path'])
        self.output_display_var = tk.StringVar(
            value=os.path.basename(self.config['output']['composite_path']))
        ttk.Entry(out_row, textvariable=self.output_display_var, state='readonly').pack(
            side='left', fill='x', expand=True)

        self.delete_source_var = tk.BooleanVar(value=self.config['output']['delete_source'])
        ttk.Checkbutton(
            source_frame,
            text='Delete source video (moves to Recycle Bin after render)',
            variable=self.delete_source_var
        ).pack(anchor='w', padx=10, pady=(2, 8))

        # --- Progress ---
        progress_frame = ttk.LabelFrame(self.frame, text='Progress')
        progress_frame.pack(fill='x', **pad)

        self.progress_var = tk.DoubleVar(value=0)
        self.progress_bar = ttk.Progressbar(
            progress_frame, variable=self.progress_var, maximum=100, length=400
        )
        self.progress_bar.pack(fill='x', padx=10, pady=(8, 4))

        self.status_var = tk.StringVar(value='Ready.')
        ttk.Label(progress_frame, textvariable=self.status_var, anchor='w').pack(
            fill='x', padx=10, pady=(0, 8)
        )

        # --- Log ---
        log_frame = ttk.LabelFrame(self.frame, text='Log')
        log_frame.pack(fill='both', expand=True, **pad)

        self.log_text = tk.Text(log_frame, height=5, state='disabled',
                                font=('Consolas', 9), wrap='word')
        log_scroll = ttk.Scrollbar(log_frame, command=self.log_text.yview)
        self.log_text.configure(yscrollcommand=log_scroll.set)
        self.log_text.pack(side='left', fill='both', expand=True, padx=5, pady=5)
        log_scroll.pack(side='right', fill='y', pady=5)

        # --- Buttons ---
        btn_row = ttk.Frame(self.frame)
        btn_row.pack(pady=(5, 10))

        self.render_btn = ttk.Button(
            btn_row,
            text='▶  Create News Ticker',
            command=self._on_render,
            style='Accent.TButton'
        )
        self.render_btn.pack(side='left', padx=10)

        ttk.Button(btn_row, text='Exit', command=self._on_exit).pack(side='left', padx=10)

        # Load saved items
        items = self.config['content']['items']
        self.items_text.insert('1.0', '\n'.join(items))

    def _browse_location(self):
        import os
        folder = filedialog.askdirectory(title='Select video location')
        if folder:
            self.location_var.set(folder)
            src = self._source_video_path_var.get()
            if src:
                base = os.path.splitext(os.path.basename(src))[0]
                out_path = os.path.join(folder, f'{base}-N.mp4')
                self._composite_path_var.set(out_path)
                self.output_display_var.set(os.path.basename(out_path))

    def _browse_source_video(self):
        import os
        initial_dir = self.location_var.get() or None
        path = filedialog.askopenfilename(
            title='Select source video',
            filetypes=[('MP4/Video', '*.mp4 *.mov *.avi *.mkv'), ('All files', '*.*')],
            initialdir=initial_dir
        )
        if path:
            self._source_video_path_var.set(path)
            self.source_display_var.set(os.path.basename(path))
            folder = self.location_var.get() or os.path.dirname(path)
            base = os.path.splitext(os.path.basename(path))[0]
            out_path = os.path.join(folder, f'{base}-N.mp4')
            self._composite_path_var.set(out_path)
            self.output_display_var.set(os.path.basename(out_path))
            if self._on_orientation_detected:
                dims = video_renderer.get_video_dimensions(path)
                if dims:
                    orientation = 'portrait' if dims[1] > dims[0] else 'landscape'
                    self._on_orientation_detected(orientation)

    def _on_exit(self):
        self.get_config()
        import config_manager
        config_manager.save(self.config)
        self.frame.winfo_toplevel().destroy()

    def _on_render(self):
        self.get_config()
        self._clear_log()
        self.progress_var.set(0)
        self.status_var.set('Starting…')
        self.render_btn.configure(state='disabled')
        threading.Thread(target=self._render_worker, daemon=True).start()
        self._poll()

    def _render_worker(self):
        try:
            engine = TickerEngine(self.config)
            engine.build()

            def progress(p):
                self._q.put(('progress', p * 100))

            def log(msg):
                self._q.put(('log', msg))

            ok, err = video_renderer.render_composite(engine, self.config, progress, log_cb=log)
            if ok and self.config['output'].get('delete_source'):
                src = self.config['output']['source_video_path']
                try:
                    import send2trash
                    send2trash.send2trash(src)
                    log(f'Source video moved to Recycle Bin: {src}')
                except Exception as e:
                    log(f'Warning: could not delete source video: {e}')
            self._q.put(('result', ok, err))
            self._q.put(('done', None))
        except Exception as e:
            self._q.put(('error', str(e)))

    def _poll(self):
        try:
            while True:
                msg = self._q.get_nowait()
                kind = msg[0]
                if kind == 'progress':
                    self.progress_var.set(msg[1])
                    self.status_var.set(f'{msg[1]:.0f}%')
                elif kind == 'log':
                    self._log(msg[1])
                elif kind == 'result':
                    ok, err = msg[1], msg[2]
                    if ok:
                        self._log('OK → ' + self.config['output']['composite_path'])
                    else:
                        self._log(f'FAILED: {err}')
                elif kind == 'done':
                    self.progress_var.set(100)
                    self.status_var.set('Done.')
                    self.render_btn.configure(state='normal')
                    return
                elif kind == 'error':
                    self._log(f'ERROR: {msg[1]}')
                    self.status_var.set('Error — see log.')
                    self.render_btn.configure(state='normal')
                    return
        except queue.Empty:
            pass
        self.frame.after(100, self._poll)

    def _log(self, text):
        self.log_text.configure(state='normal')
        self.log_text.insert('end', text + '\n')
        self.log_text.see('end')
        self.log_text.configure(state='disabled')

    def _clear_log(self):
        self.log_text.configure(state='normal')
        self.log_text.delete('1.0', 'end')
        self.log_text.configure(state='disabled')

    def apply_to_config(self):
        raw = self.items_text.get('1.0', 'end-1c')
        items = [line for line in raw.splitlines() if line.strip()]
        self.config['content']['items'] = items
        self.config['content']['label'] = self.label_var.get().strip()
        self.config['output']['start_time']    = float(self.start_var.get())
        self.config['output']['end_time']      = float(self.end_var.get())
        self.config['output']['loop']          = self.loop_var.get()
        self.config['output']['location']      = self.location_var.get()
        self.config['output']['delete_source'] = self.delete_source_var.get()
        for key in ('source_video_path', 'composite_path'):
            self.config['output'][key] = getattr(self, f'_{key}_var').get()
