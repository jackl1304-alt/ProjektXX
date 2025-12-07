from __future__ import annotations

import logging
import os
import tempfile
from pathlib import Path
from typing import Iterable
from uuid import uuid4

import ffmpeg

LOGGER = logging.getLogger(__name__)
DEBUG_FFMPEG = os.environ.get("FFMPEG_DEBUG", "").lower() in {"1", "true", "yes"}

DEFAULT_LOUDNESS = {"target_i": -16.0, "target_tp": -1.5, "target_lra": 11.0}
WATERMARK_POSITIONS = {
    "top-left": ("{margin}", "{margin}"),
    "top-right": ("W-w-{margin}", "{margin}"),
    "bottom-left": ("{margin}", "H-h-{margin}"),
    "bottom-right": ("W-w-{margin}", "H-h-{margin}"),
    "center": ("(W-w)/2", "(H-h)/2"),
}


def _has_audio_track(path: Path) -> bool:
    """Prüft, ob ein Video bereits einen Audiostream enthält."""
    try:
        probe = ffmpeg.probe(path.as_posix())
    except ffmpeg.Error as exc:
        LOGGER.warning("Render: Audio-Probe fehlgeschlagen (%s) – generiere Stille.", exc)
        return False
    return any(stream.get("codec_type") == "audio" for stream in probe.get("streams", []))


def _ensure_audio(stream, has_audio: bool):
    """Stellt sicher, dass ein Audiostream vorhanden ist."""
    if has_audio and stream.audio is not None:
        return stream.audio
    LOGGER.debug("Render: Erzeuge künstlichen Audiostream (anullsrc).")
    return ffmpeg.input("anullsrc=channel_layout=stereo:sample_rate=44100", f="lavfi").audio


def _loudnorm(audio_stream, loudness_cfg: dict[str, float]):
    loudnorm = {**DEFAULT_LOUDNESS, **(loudness_cfg or {})}
    return audio_stream.filter(
        "loudnorm",
        I=loudnorm["target_i"],
        TP=loudnorm["target_tp"],
        LRA=loudnorm["target_lra"],
    )


def _prepare_segment(
    input_path: Path,
    output_dir: Path,
    width: int,
    height: int,
    fps: int,
    loudness_cfg: dict[str, float],
    settings: dict,
) -> Path:
    """Normalisiert Video-/Audioeinstellungen einer Sequenz."""
    output_dir.mkdir(parents=True, exist_ok=True)
    prepared_path = output_dir / f"segment_{uuid4().hex}.mp4"

    LOGGER.debug("Render: Normalisiere Clip %s", input_path)
    has_audio = _has_audio_track(input_path)
    stream = ffmpeg.input(input_path.as_posix())

    video = stream.video.filter("scale", width, -2).filter(
        "pad",
        width,
        height,
        "(ow-iw)/2",
        "(oh-ih)/2",
        color=settings.get("render_padding_color", "black"),
    )
    video = video.filter("fps", fps)

    audio = _ensure_audio(stream, has_audio)
    audio = _loudnorm(audio, loudness_cfg)

    output_args = {
        "preset": settings.get("render_preset", "medium"),
        "movflags": "+faststart",
        "pix_fmt": "yuv420p",
        "r": fps,
        "ac": 2,
        **{"b:v": settings.get("render_video_bitrate", "6000k")},
        **{"b:a": settings.get("render_audio_bitrate", "192k")},
    }

    (
        ffmpeg.output(video, audio, prepared_path.as_posix(), **output_args)
        .overwrite_output()
        .run(quiet=not DEBUG_FFMPEG)
    )

    return prepared_path


def _optional_segment(path_value: str | None, label: str) -> Path | None:
    if not path_value:
        return None
    path = Path(path_value)
    if path.exists():
        return path
    LOGGER.warning("Render: %s %s nicht gefunden – übersprungen.", label, path)
    return None


def _assemble_segments(video_paths: Iterable[str], settings: dict) -> list[Path]:
    segments: list[Path] = []

    intro = _optional_segment(settings.get("render_intro_path"), "Intro")
    if intro:
        segments.append(intro)

    for clip in video_paths:
        clip_path = Path(clip)
        if clip_path.exists():
            segments.append(clip_path)
        else:
            LOGGER.warning("Render: Clip %s existiert nicht – übersprungen.", clip_path)

    outro = _optional_segment(settings.get("render_outro_path"), "Outro")
    if outro:
        segments.append(outro)

    return segments


def _concat_segments(segment_paths: list[Path], temp_dir: Path) -> Path:
    with tempfile.NamedTemporaryFile("w", delete=False, suffix=".txt") as concat_file:
        for clip in segment_paths:
            concat_file.write(f"file '{clip.as_posix()}'\n")
        concat_list_path = concat_file.name

    concatenated = temp_dir / f"concat_{uuid4().hex}.mp4"

    try:
        (
            ffmpeg.input(concat_list_path, format="concat", safe=0)
            .output(concatenated.as_posix(), c="copy", movflags="+faststart")
            .overwrite_output()
            .run(quiet=not DEBUG_FFMPEG)
        )
    finally:
        try:
            os.remove(concat_list_path)
        except OSError:
            LOGGER.warning("Render: Temp-Datei %s konnte nicht gelöscht werden.", concat_list_path)

    return concatenated


def _apply_watermark(video_stream, watermark_cfg: dict, width: int):
    if not watermark_cfg:
        return video_stream

    watermark_path = watermark_cfg.get("path")
    if not watermark_path:
        return video_stream

    path = Path(watermark_path)
    if not path.exists():
        LOGGER.warning("Render: Wasserzeichen %s nicht gefunden – übersprungen.", path)
        return video_stream

    margin = int(watermark_cfg.get("margin", 40))
    position = watermark_cfg.get("position", "top-right")
    x_expr, y_expr = WATERMARK_POSITIONS.get(
        position,
        WATERMARK_POSITIONS["top-right"],
    )

    overlay = ffmpeg.input(path.as_posix())
    target_width = watermark_cfg.get("width")
    if isinstance(target_width, (int, float)) and target_width > 0:
        overlay = overlay.filter("scale", int(target_width), -1)
    elif isinstance(watermark_cfg.get("relative_width"), (int, float)):
        relative = watermark_cfg["relative_width"]
        overlay = overlay.filter("scale", int(width * relative), -1)

    opacity = watermark_cfg.get("opacity", 1.0)
    if opacity < 1.0:
        overlay = overlay.filter("format", "rgba").filter("colorchannelmixer", aa=opacity)

    x = x_expr.format(margin=margin)
    y = y_expr.format(margin=margin)
    return ffmpeg.overlay(video_stream, overlay, x=x, y=y)


def _mix_background_audio(audio_stream, music_cfg: dict | None):
    if not music_cfg:
        return audio_stream
    music_path = music_cfg.get("path")
    if not music_path:
        return audio_stream

    path = Path(music_path)
    if not path.exists():
        LOGGER.warning("Render: Hintergrundmusik %s nicht gefunden – übersprungen.", path)
        return audio_stream

    volume = float(music_cfg.get("volume", 0.1))
    music_stream = ffmpeg.input(path.as_posix(), stream_loop=-1).audio.filter("volume", volume)

    ducking = music_cfg.get("ducking")
    if isinstance(ducking, (int, float)) and 0 < ducking < 1:
        audio_stream = audio_stream.filter("volume", ducking)

    return ffmpeg.filter(
        [audio_stream, music_stream],
        "amix",
        inputs=2,
        duration="shortest",
        dropout_transition=2,
    )


def render_videos(
    video_paths: Iterable[str],
    output_path: str,
    *,
    vertical: bool = True,
    fps: int = 30,
    settings: dict | None = None,
) -> str:
    """Erstellt eine Compilation inkl. Intro/Outro, Wasserzeichen und Audio-Mix."""
    resolved_output = Path(output_path)
    resolved_output.parent.mkdir(parents=True, exist_ok=True)

    settings = settings or {}

    target_width, target_height = (1080, 1920) if vertical else (1920, 1080)
    loudness_cfg = settings.get("render_loudness", {})

    raw_segments = _assemble_segments(video_paths, settings)
    if not raw_segments:
        raise ValueError("Keine gültigen Videos zum Rendern übergeben.")

    LOGGER.info("Render: Bereite %s Segmente vor.", len(raw_segments))

    temp_dir = Path(settings.get("temp_folder", "./temp"))
    prepared_segments: list[Path] = []
    concatenated: Path | None = None
    try:
        for segment in raw_segments:
            prepared_segments.append(
                _prepare_segment(
                    segment,
                    temp_dir,
                    target_width,
                    target_height,
                    fps,
                    loudness_cfg,
                    settings,
                )
            )

        concatenated = _concat_segments(prepared_segments, temp_dir)

        LOGGER.info("Render: Wende Template-Effekte an und schreibe %s", resolved_output)

        final_stream = ffmpeg.input(concatenated.as_posix())
        video_stream = final_stream.video
        audio_stream = _ensure_audio(final_stream)

        video_stream = _apply_watermark(video_stream, settings.get("render_watermark"), target_width)
        audio_stream = _mix_background_audio(audio_stream, settings.get("render_background_music"))
        audio_stream = _loudnorm(audio_stream, loudness_cfg)

        output_args = {
            "preset": settings.get("render_preset", "medium"),
            "movflags": "+faststart",
            "pix_fmt": "yuv420p",
            "r": fps,
            "ac": 2,
            **{"b:v": settings.get("render_video_bitrate", "6000k")},
            **{"b:a": settings.get("render_audio_bitrate", "192k")},
        }

        (
            ffmpeg.output(video_stream, audio_stream, resolved_output.as_posix(), **output_args)
            .overwrite_output()
            .run(quiet=True)
        )
    finally:
        for path in prepared_segments:
            try:
                path.unlink(missing_ok=True)
            except OSError:
                LOGGER.debug("Render: temporäre Datei %s konnte nicht gelöscht werden.", path)
        if concatenated is not None:
            try:
                concatenated.unlink(missing_ok=True)
            except OSError:
                LOGGER.debug("Render: concatenated Datei %s konnte nicht gelöscht werden.", concatenated)

    LOGGER.info("Render: Ausgabe gespeichert in %s", resolved_output)
    return resolved_output.as_posix()