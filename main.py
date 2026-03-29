import tkinter as tk
from tkinter import ttk

import config_manager
from ui.content_tab import ContentTab
from ui.style_tab   import StyleTab


class NewsTickerApp:
    def __init__(self, root):
        self.root = root
        self.root.title('NewsTicker')
        self.root.minsize(700, 580)
        self.root.resizable(True, True)

        self.config = config_manager.load()

        self._build_ui()
        self.root.protocol('WM_DELETE_WINDOW', self._on_close)

    def _build_ui(self):
        self.notebook = ttk.Notebook(self.root)
        self.notebook.pack(fill='both', expand=True, padx=8, pady=8)

        self.content_tab = ContentTab(self.notebook, self.config, self._collect_all)
        self.style_tab   = StyleTab(self.notebook, self.config)
        self.content_tab._on_orientation_detected = self.style_tab.apply_orientation_presets

    def _collect_all(self):
        """Flush all tab widgets into self.config."""
        self.content_tab.apply_to_config()
        self.style_tab.apply_to_config()

    def _on_close(self):
        self._collect_all()
        config_manager.save(self.config)
        self.root.destroy()


def main():
    root = tk.Tk()

    # Use a clean ttk theme
    style = ttk.Style()
    available = style.theme_names()
    for preferred in ('vista', 'winnative', 'clam', 'alt', 'default'):
        if preferred in available:
            style.theme_use(preferred)
            break

    app = NewsTickerApp(root)
    root.mainloop()


if __name__ == '__main__':
    main()
