import json
import os
import copy

CONFIG_PATH = os.path.join(os.path.dirname(__file__), 'ticker_config.json')

DEFAULTS = {
    "content": {
        "items": ["News item one", "News item two", "News item three"],
        "label": "",
        "logo_path": "",
        "logo_enabled": False,
        "right_logo_path": "",
        "right_logo_enabled": False
    },
    "style": {
        "bar_color": "#CC0000",
        "text_color": "#FFFFFF",
        "separator_color": "#FFFF00",
        "label_color": "#FFFFFF",
        "font_path": "",
        "font_size": 32,
        "bar_height": 60,
        "scroll_speed": 150,
        "logo_spin_speed": 45
    },
    "output": {
        "start_time": 5,
        "end_time": 55,
        "loop": False,
        "location": "",
        "source_video_path": "",
        "composite_path": "",
        "delete_source": False
    },
    "render": {},
    "style_landscape": {
        "font_size": 32,
        "bar_height": 60,
        "scroll_speed": 150,
        "logo_spin_speed": 45
    },
    "style_portrait": {
        "font_size": 72,
        "bar_height": 120,
        "scroll_speed": 150,
        "logo_spin_speed": 45
    }
}


def load():
    if os.path.exists(CONFIG_PATH):
        try:
            with open(CONFIG_PATH, 'r', encoding='utf-8') as f:
                saved = json.load(f)
            return _merge(DEFAULTS, saved)
        except Exception:
            pass
    return copy.deepcopy(DEFAULTS)


def save(config):
    with open(CONFIG_PATH, 'w', encoding='utf-8') as f:
        json.dump(config, f, indent=2, ensure_ascii=False)


def _merge(defaults, saved):
    result = copy.deepcopy(defaults)
    for key, val in saved.items():
        if key in result and isinstance(result[key], dict) and isinstance(val, dict):
            result[key] = _merge(result[key], val)
        else:
            result[key] = val
    return result
