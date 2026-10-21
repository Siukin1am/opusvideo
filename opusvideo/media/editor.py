"""The Editor: assembles clips into the final cut with subtitles (local ffmpeg, no API)."""

from __future__ import annotations

import subprocess
from pathlib import Path

from ..schemas import Shot

TARGET = {"16:9": (1280, 720), "9:16": (720, 1280), "1:1": (1024, 1024)}


def _ts(seconds: float) -> str:
    ms = int(round(seconds * 1000))
    h, ms = divmod(ms, 3_600_000)
    m, ms = divmod(ms, 60_000)
    s, ms = divmod(ms, 1000)
    return f"{h:02}:{m:02}:{s:02},{ms:03}"


def probe_duration(path: Path) -> float:
    out = subprocess.run(["ffprobe", "-v", "error", "-show_entries", "format=duration",
                          "-of", "default=nw=1:nk=1", str(path)],
                         capture_output=True, text=True, check=True).stdout.strip()
    return float(out)


def write_srt(shots: list[Shot], durations: list[float], out_path: Path) -> Path:
    """Spread each shot's dialogue evenly across that shot's actual clip length."""
    entries, t, n = [], 0.0, 1
    for shot, dur in zip(shots, durations):
        lines = [l for l in shot.dialogue if l.text.strip()]
        if lines:
            slot = dur / len(lines)
            for i, line in enumerate(lines):
                start, end = t + i * slot, t + (i + 1) * slot - 0.05
                entries.append(f"{n}\n{_ts(start)} --> {_ts(end)}\n{line.character}: {line.text}\n")
                n += 1
        t += dur
    out_path.write_text("\n".join(entries), encoding="utf-8")
    return out_path


def assemble(clips: list[Path], shots: list[Shot], out_path: Path, aspect_ratio: str = "16:9") -> Path:
    """Normalise every clip to one size/fps, concatenate, and mux soft subtitles."""
    w, h = TARGET.get(aspect_ratio, TARGET["16:9"])
    work = out_path.parent / "edit"
    work.mkdir(parents=True, exist_ok=True)
    normalised = []
    for i, clip in enumerate(clips):
        dst = work / f"{i:03}.mp4"
        subprocess.run(
            ["ffmpeg", "-y", "-loglevel", "error", "-i", str(clip), "-an",
             "-vf", f"scale={w}:{h}:force_original_aspect_ratio=decrease,"
                    f"pad={w}:{h}:(ow-iw)/2:(oh-ih)/2,fps=24,format=yuv420p",
             "-c:v", "libx264", str(dst)],
            check=True,
        )
        normalised.append(dst)

    concat_list = work / "concat.txt"
    concat_list.write_text("".join(f"file '{p.resolve()}'\n" for p in normalised))
    silent = work / "silent.mp4"
    subprocess.run(["ffmpeg", "-y", "-loglevel", "error", "-f", "concat", "-safe", "0",
                    "-i", str(concat_list), "-c", "copy", str(silent)], check=True)

    srt = write_srt(shots, [probe_duration(p) for p in normalised], out_path.with_suffix(".srt"))
    subprocess.run(["ffmpeg", "-y", "-loglevel", "error", "-i", str(silent), "-i", str(srt),
                    "-c:v", "copy", "-c:s", "mov_text", "-metadata:s:s:0", "language=eng",
                    str(out_path)], check=True)
    return out_path
