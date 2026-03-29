import json
import os
import subprocess
import tempfile
import threading

try:
    import imageio_ffmpeg
    _FFMPEG = imageio_ffmpeg.get_ffmpeg_exe()
except Exception:
    _FFMPEG = 'ffmpeg'  # fall back to PATH


def _ensure_dir(path):
    d = os.path.dirname(path)
    if d and not os.path.exists(d):
        os.makedirs(d, exist_ok=True)


def _even(n):
    """yuv420p requires even dimensions."""
    return n if n % 2 == 0 else n + 1


def _get_ffprobe():
    """Return path to ffprobe that lives alongside the known ffmpeg binary."""
    ffmpeg_dir = os.path.dirname(_FFMPEG)
    for name in ('ffprobe.exe', 'ffprobe'):
        candidate = os.path.join(ffmpeg_dir, name)
        if os.path.exists(candidate):
            return candidate
    return None


def get_video_duration(source_path):
    """Return duration in seconds of source_path, or None if it cannot be determined."""
    ffprobe = _get_ffprobe()
    if ffprobe:
        try:
            result = subprocess.run(
                [ffprobe, '-v', 'quiet',
                 '-show_entries', 'format=duration',
                 '-of', 'csv=p=0',
                 source_path],
                stdout=subprocess.PIPE,
                stderr=subprocess.DEVNULL,
                text=True
            )
            if result.returncode == 0 and result.stdout.strip():
                return float(result.stdout.strip())
        except Exception:
            pass
    return None


def get_video_dimensions(source_path):
    """
    Return (width, height) of the first video stream in source_path.
    Returns None if the dimensions cannot be determined.
    """
    import re

    # Prefer ffprobe — clean, machine-readable output
    ffprobe = _get_ffprobe()
    if ffprobe:
        try:
            result = subprocess.run(
                [ffprobe, '-v', 'quiet',
                 '-select_streams', 'v:0',
                 '-show_entries', 'stream=width,height',
                 '-of', 'csv=p=0',
                 source_path],
                stdout=subprocess.PIPE,
                stderr=subprocess.DEVNULL,
                text=True
            )
            if result.returncode == 0 and result.stdout.strip():
                parts = result.stdout.strip().split(',')
                if len(parts) >= 2:
                    return int(parts[0]), int(parts[1])
        except Exception:
            pass

    # Fallback: parse "WxH" from ffmpeg -i stderr
    try:
        result = subprocess.run(
            [_FFMPEG, '-i', source_path],
            stdout=subprocess.DEVNULL,
            stderr=subprocess.PIPE,
            text=True
        )
        match = re.search(r'Video:.*?(\d{3,5})x(\d{3,5})', result.stderr, re.DOTALL)
        if match:
            return int(match.group(1)), int(match.group(2))
    except Exception:
        pass

    return None


def get_video_fps(source_path):
    """
    Return the FPS of the first video stream in source_path as a float.
    Returns None if it cannot be determined.
    """
    import re

    ffprobe = _get_ffprobe()
    if ffprobe:
        try:
            result = subprocess.run(
                [ffprobe, '-v', 'quiet',
                 '-select_streams', 'v:0',
                 '-show_entries', 'stream=r_frame_rate',
                 '-of', 'csv=p=0',
                 source_path],
                stdout=subprocess.PIPE,
                stderr=subprocess.DEVNULL,
                text=True
            )
            if result.returncode == 0 and result.stdout.strip():
                raw = result.stdout.strip()
                if '/' in raw:
                    num, den = raw.split('/')
                    if int(den) != 0:
                        return float(int(num) / int(den))
                else:
                    return float(raw)
        except Exception:
            pass

    # Fallback: parse fps from ffmpeg -i stderr
    try:
        result = subprocess.run(
            [_FFMPEG, '-i', source_path],
            stdout=subprocess.DEVNULL,
            stderr=subprocess.PIPE,
            text=True
        )
        match = re.search(r'(\d+(?:\.\d+)?)\s+fps', result.stderr)
        if match:
            return float(match.group(1))
    except Exception:
        pass

    return None


def _render_ticker_bar(engine, config, progress_cb=None, output_path=None, width_override=None, fps_override=None, duration_override=None, log_cb=None):
    """
    Internal: render the ticker bar frames to an MP4 file.
    progress_cb(float 0..1) is called periodically.
    Returns (True, '') on success or (False, error_msg) on failure.
    """
    def log(msg):
        if log_cb:
            log_cb(msg)

    output = config['output']
    style = config['style']

    width = width_override or 1920  # always provided by render_composite; 1920 as safety fallback
    bar_height = _even(style['bar_height'])
    width = _even(width)
    fps = fps_override or 25  # always provided by render_composite; 25 as safety fallback
    if duration_override is not None:
        duration = max(duration_override, 1.0)
    else:
        start_time = float(output['start_time'])
        end_time = float(output['end_time'])
        duration = max(end_time - start_time, 1.0)
    total_frames = int(duration * fps)

    log(f'Ticker bar: {width}x{bar_height}px, {duration:.1f}s, {total_frames} frames @ {fps:.2f} fps')

    if not output_path:
        return False, "No output path provided."
    _ensure_dir(output_path)

    cmd = [
        _FFMPEG, '-y',
        '-f', 'rawvideo',
        '-vcodec', 'rawvideo',
        '-s', f'{width}x{bar_height}',
        '-pix_fmt', 'rgb24',
        '-r', str(fps),
        '-i', 'pipe:0',
        '-c:v', 'libx264',
        '-pix_fmt', 'yuv420p',
        '-preset', 'fast',
        output_path
    ]

    log(f'FFmpeg (ticker): {" ".join(cmd)}')

    try:
        proc = subprocess.Popen(
            cmd,
            stdin=subprocess.PIPE,
            stdout=subprocess.DEVNULL,
            stderr=subprocess.PIPE
        )
    except FileNotFoundError:
        return False, f"FFmpeg not found: {_FFMPEG}"

    stderr_lines = []
    def _read_stderr():
        for line in proc.stderr:
            stderr_lines.append(line.decode('utf-8', errors='replace').rstrip())
    stderr_thread = threading.Thread(target=_read_stderr, daemon=True)
    stderr_thread.start()

    try:
        for i in range(total_frames):
            t = i / fps
            frame = engine.get_frame(t, width)
            proc.stdin.write(frame.tobytes())
            if progress_cb and i % max(1, total_frames // 100) == 0:
                progress_cb(i / total_frames)
        proc.stdin.close()
        proc.wait()
    except BrokenPipeError:
        proc.stdin.close()
        proc.wait()
        stderr_thread.join(timeout=2)
        err_text = '\n'.join(stderr_lines[-20:])
        return False, f"FFmpeg pipe error:\n{err_text}"
    except Exception as e:
        proc.stdin.close()
        proc.kill()
        stderr_thread.join(timeout=2)
        return False, str(e)

    stderr_thread.join(timeout=2)

    if proc.returncode != 0:
        err_text = '\n'.join(stderr_lines[-20:])
        return False, f"FFmpeg exited with code {proc.returncode}:\n{err_text}"

    if progress_cb:
        progress_cb(1.0)
    log(f'Ticker bar written to: {output_path}')
    return True, ''


def render_composite(engine, config, progress_cb=None, log_cb=None):
    """
    Render the ticker burned onto the source video.
    Renders the ticker bar to a temp file first, then overlays with FFmpeg.
    Returns (True, '') on success or (False, error_msg) on failure.
    """
    def log(msg):
        if log_cb:
            log_cb(msg)

    output = config['output']
    source = output['source_video_path']
    composite_out = output['composite_path']
    start_time = float(output['start_time'])
    end_time = float(output['end_time'])
    loop = output.get('loop', False)

    log(f'Source: {source}')

    if not source or not os.path.exists(source):
        return False, "Source video not found."
    if not composite_out:
        return False, "No output path set."

    _ensure_dir(composite_out)

    # Auto-detect source video dimensions and FPS so the ticker matches exactly
    dims = get_video_dimensions(source)
    src_width = dims[0] if dims else None
    src_height = dims[1] if dims else None
    src_fps = get_video_fps(source)

    if src_width and src_height and src_fps:
        log(f'Detected: {src_width}x{src_height} @ {src_fps:.2f} fps')
    else:
        log(f'Could not detect dimensions/fps — using fallbacks (1920px, 25fps)')

    if loop:
        ticker_duration = max(end_time - start_time, 1.0)
        ticker_end = end_time
        log(f'Ticker window: {start_time}s → {ticker_end}s (loop)')
    else:
        ticker_duration = engine.content_duration(src_width or 1920)
        ticker_end = start_time + ticker_duration
        log(f'Ticker window: {start_time}s → {ticker_end:.2f}s (one pass, {ticker_duration:.2f}s)')

    # Step 1: render ticker bar to temp file (0–70% of progress)
    tmp_fd, tmp_path = tempfile.mkstemp(suffix='.mp4')
    os.close(tmp_fd)
    log(f'Step 1/2: Rendering ticker bar…')

    def ticker_progress(p):
        if progress_cb:
            progress_cb(p * 0.70)

    ok, err = _render_ticker_bar(engine, config, ticker_progress,
                                  output_path=tmp_path, width_override=src_width,
                                  fps_override=src_fps, duration_override=ticker_duration,
                                  log_cb=log_cb)
    if not ok:
        _safe_delete(tmp_path)
        return False, f"Ticker render failed: {err}"

    # Step 2: overlay onto source video (70–100% of progress)
    log(f'Step 2/2: Compositing ticker onto source video…')

    filter_complex = (
        f"[1:v]setpts=PTS+{start_time}/TB[ticker];"
        f"[0:v][ticker]overlay=0:H-h:enable='between(t,{start_time},{ticker_end})'"
    )

    cmd = [
        _FFMPEG, '-y',
        '-i', source,
        '-i', tmp_path,
        '-filter_complex', filter_complex,
        '-c:v', 'libx264',
        '-preset', 'fast',
        '-pix_fmt', 'yuv420p',
        '-c:a', 'copy',
        composite_out
    ]

    log(f'FFmpeg (composite): {" ".join(cmd)}')

    if progress_cb:
        progress_cb(0.75)

    try:
        result = subprocess.run(
            cmd,
            stdout=subprocess.DEVNULL,
            stderr=subprocess.PIPE,
            text=True
        )
    except FileNotFoundError:
        _safe_delete(tmp_path)
        return False, f"FFmpeg not found: {_FFMPEG}"

    _safe_delete(tmp_path)

    if result.returncode != 0:
        return False, f"Composite FFmpeg failed:\n{result.stderr[-1000:]}"

    log(f'Output: {composite_out}')

    # Write companion JSON for interactive web player
    timings = engine.get_item_timings(src_width or 1920)
    if timings:
        for entry in timings:
            entry['start'] = round(entry['start'] + start_time, 2)
            entry['end'] = round(entry['end'] + start_time, 2)
        json_path = os.path.splitext(composite_out)[0] + '.json'
        try:
            with open(json_path, 'w', encoding='utf-8') as f:
                json.dump(timings, f, indent=2, ensure_ascii=False)
            log(f'Interactive JSON: {json_path}')
        except Exception as e:
            log(f'Warning: could not write JSON: {e}')

    if progress_cb:
        progress_cb(1.0)
    return True, ''


def _safe_delete(path):
    try:
        os.remove(path)
    except Exception:
        pass
