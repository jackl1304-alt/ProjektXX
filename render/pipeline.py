"""Video-Rendering-Pipeline mit FFmpeg.

Orchestriert die Erstellung von Video-Compilations mit:
- Intro/Outro-Verarbeitung
- Wasserzeichen-Overlay
- Hintergrundmusik mit Audio-Ducking
- Loudness-Normalisierung (EBU R128)
- Multi-Format Support (vertikal/horizontal)
"""

from __future__ import annotations

import logging
import os
import tempfile
from pathlib import Path
from typing import Any, Dict, Iterable, Optional, Tuple
from uuid import uuid4

import ffmpeg

logger = logging.getLogger(__name__)

# Debug-Flag für FFmpeg-Ausgabe
DEBUG_FFMPEG = os.environ.get("FFMPEG_DEBUG", "").lower() in {"1", "true", "yes"}

# EBU R128 Loudness Standard
DEFAULT_LOUDNESS: Dict[str, float] = {
    "target_i": -16.0,  # Integrated Loudness
    "target_tp": -1.5,  # True Peak
    "target_lra": 11.0,  # Loudness Range
}

# Wasserzeichen-Positionen (x, y Koordinaten)
WATERMARK_POSITIONS: Dict[str, Tuple[str, str]] = {
    "top-left": ("{margin}", "{margin}"),
    "top-right": ("W-w-{margin}", "{margin}"),
    "bottom-left": ("{margin}", "H-h-{margin}"),
    "bottom-right": ("W-w-{margin}", "H-h-{margin}"),
    "center": ("(W-w)/2", "(H-h)/2"),
}

# Video-Formate
VERTICAL_FORMAT: Tuple[int, int] = (1080, 1920)  # 9:16 für mobile
HORIZONTAL_FORMAT: Tuple[int, int] = (1920, 1080)  # 16:9 für Desktop


class RenderError(Exception):
    """Exception für Rendering-Fehler."""

    pass


class FFmpegError(RenderError):
    """Exception für FFmpeg-Fehler."""

    pass


def _has_audio_track(path: Path) -> bool:
    """Prüft ob ein Video einen Audiostream enthält.

    Args:
        path: Pfad zur Video-Datei

    Returns:
        True wenn Audiostream vorhanden, sonst False

    Logs:
        DEBUG: Probe-Ergebnis
        WARNING: Probe-Fehler
    """
    try:
        probe = ffmpeg.probe(path.as_posix())
        has_audio = any(
            stream.get("codec_type") == "audio" for stream in probe.get("streams", [])
        )
        logger.debug(f"Audio-Track Probe: {path.name} → {has_audio}")
        return has_audio
    except ffmpeg.Error as exc:
        logger.warning(
            f"Audio-Probe fehlgeschlagen für {path.name} – "
            f"generiere künstlichen Audiostream: {exc}"
        )
        return False


def _ensure_audio(stream: Any, has_audio: bool) -> Any:
    """Stellt sicher dass ein Audiostream vorhanden ist.

    Falls das Video keinen Audio hat, wird ein künstlicher
    Stille-Audiostream (anullsrc) generiert.

    Args:
        stream: FFmpeg Stream-Objekt
        has_audio: Boolean ob Audio vorhanden ist

    Returns:
        Audio-Stream (entweder vom Video oder künstlich generiert)
    """
    if has_audio and stream.audio is not None:
        return stream.audio

    logger.debug("Erzeuge künstlichen Audiostream (anullsrc)")
    return ffmpeg.input(
        "anullsrc=channel_layout=stereo:sample_rate=44100", f="lavfi"
    ).audio


def _loudnorm(
    audio_stream: Any, loudness_cfg: Optional[Dict[str, float]]
) -> Any:
    """Normalisiert Audio-Lautstärke nach EBU R128 Standard.

    Args:
        audio_stream: FFmpeg Audio-Stream
        loudness_cfg: Konfiguration mit target_i, target_tp, target_lra

    Returns:
        FFmpeg Filter-Chain mit loudnorm-Filter
    """
    loudnorm_cfg = {**DEFAULT_LOUDNESS, **(loudness_cfg or {})}
    return audio_stream.filter(
        "loudnorm",
        I=loudnorm_cfg["target_i"],
        TP=loudnorm_cfg["target_tp"],
        LRA=loudnorm_cfg["target_lra"],
    )


def _prepare_segment(
    input_path: Path,
    output_dir: Path,
    width: int,
    height: int,
    fps: int,
    loudness_cfg: Optional[Dict[str, float]],
    settings: Dict[str, Any],
) -> Path:
    """Normalisiert Video- und Audio-Einstellungen eines Clips.

    Implementiert:
    - Video-Skalierung und Padding (um aspect ratio zu erhalten)
    - Audio-Stream-Erzeugung (falls nicht vorhanden)
    - Loudness-Normalisierung

    Args:
        input_path: Pfad zum Input-Video
        output_dir: Zielverzeichnis für normalisiertes Video
        width: Ziel-Video-Breite
        height: Ziel-Video-Höhe
        fps: Frames per Second
        loudness_cfg: Loudness-Konfiguration
        settings: Rendering-Settings (preset, bitrate, color, etc.)

    Returns:
        Pfad zum normalisierten Video

    Raises:
        FFmpegError: Bei FFmpeg-Fehler

    Logs:
        DEBUG: Normalisierungs-Details
        ERROR: FFmpeg-Fehler
    """
    try:
        output_dir.mkdir(parents=True, exist_ok=True)
        prepared_path = output_dir / f"segment_{uuid4().hex}.mp4"

        logger.debug(f"Normalisiere Clip: {input_path.name} → {width}x{height} @ {fps}fps")

        has_audio = _has_audio_track(input_path)
        stream = ffmpeg.input(input_path.as_posix())

        # Video-Stream: Scale + Pad
        video = stream.video.filter("scale", width, -2).filter(
            "pad",
            width,
            height,
            "(ow-iw)/2",
            "(oh-ih)/2",
            color=settings.get("render_padding_color", "black"),
        )
        video = video.filter("fps", fps)

        # Audio-Stream: Ensure + Loudnorm
        audio = _ensure_audio(stream, has_audio)
        audio = _loudnorm(audio, loudness_cfg)

        # FFmpeg Output-Parameter
        output_args: Dict[str, Any] = {
            "preset": settings.get("render_preset", "medium"),
            "movflags": "+faststart",
            "pix_fmt": "yuv420p",
            "r": fps,
            "ac": 2,
            "b:v": settings.get("render_video_bitrate", "6000k"),
            "b:a": settings.get("render_audio_bitrate", "192k"),
        }

        logger.debug(f"FFmpeg Output-Args: {output_args}")

        (
            ffmpeg.output(video, audio, prepared_path.as_posix(), **output_args)
            .overwrite_output()
            .run(quiet=not DEBUG_FFMPEG)
        )

        logger.debug(f"Segment normalisiert: {prepared_path.name}")
        return prepared_path

    except ffmpeg.Error as exc:
        error_msg = f"FFmpeg-Fehler bei Clip-Normalisierung: {input_path.name} - {exc}"
        logger.error(error_msg, exc_info=True)
        raise FFmpegError(error_msg) from exc
    except Exception as exc:
        error_msg = f"Fehler bei Clip-Normalisierung: {input_path.name} - {exc}"
        logger.error(error_msg, exc_info=True)
        raise RenderError(error_msg) from exc


def _optional_segment(path_value: Optional[str], label: str) -> Optional[Path]:
    """Validiert optionale Segment-Dateien (Intro, Outro, etc.).

    Args:
        path_value: Pfad als String oder None
        label: Label für Logging (z.B. "Intro", "Outro")

    Returns:
        Path-Objekt falls existiert, sonst None

    Logs:
        DEBUG: Datei vorhanden
        WARNING: Datei nicht gefunden
    """
    if not path_value:
        return None

    path = Path(path_value)
    if path.exists():
        logger.debug(f"{label} gefunden: {path.name}")
        return path

    logger.warning(f"{label} nicht gefunden: {path} – übersprungen")
    return None


def _assemble_segments(
    video_paths: Iterable[str], settings: Dict[str, Any]
) -> list[Path]:
    """Assembliert Video-Segmente mit optionalen Intro/Outro.

    Reihenfolge:
    1. Intro (optional)
    2. Alle Clips (in angegebener Reihenfolge)
    3. Outro (optional)

    Args:
        video_paths: Iterable mit Pfaden zu Video-Clips
        settings: Settings mit Keys "render_intro_path", "render_outro_path"

    Returns:
        Liste mit angeordneten Path-Objekten

    Logs:
        DEBUG: Anzahl Segmente
        WARNING: Nicht-existierende Dateien
    """
    segments: list[Path] = []

    # Intro hinzufügen
    intro = _optional_segment(settings.get("render_intro_path"), "Intro")
    if intro:
        segments.append(intro)

    # Clips hinzufügen
    for clip in video_paths:
        clip_path = Path(clip)
        if clip_path.exists():
            segments.append(clip_path)
        else:
            logger.warning(f"Clip nicht gefunden: {clip_path} – übersprungen")

    # Outro hinzufügen
    outro = _optional_segment(settings.get("render_outro_path"), "Outro")
    if outro:
        segments.append(outro)

    logger.debug(f"Assembled {len(segments)} Segmente (Intro + {len(list(video_paths))} Clips + Outro)")
    return segments


def _concat_segments(segment_paths: list[Path], temp_dir: Path) -> Path:
    """Konkateniert mehrere Video-Segmente zu einem Video.

    Nutzt FFmpeg concat demuxer für verlustfreien Zusammenschnitt.

    Args:
        segment_paths: Liste mit Video-Dateien
        temp_dir: Temp-Verzeichnis für Concat-Datei

    Returns:
        Pfad zur konkatierten Video-Datei

    Raises:
        FFmpegError: Bei FFmpeg-Fehler
        RenderError: Bei sonstigen Fehlern

    Logs:
        DEBUG: Concat-Datei-Details
        ERROR: FFmpeg-Fehler
    """
    try:
        # Erstelle Concat-Datei
        with tempfile.NamedTemporaryFile(
            "w", delete=False, suffix=".txt"
        ) as concat_file:
            for clip in segment_paths:
                concat_file.write(f"file '{clip.as_posix()}'\n")
            concat_list_path = concat_file.name

        logger.debug(f"Concat-Datei erstellt: {concat_list_path}")

        concatenated = temp_dir / f"concat_{uuid4().hex}.mp4"

        logger.info(
            f"Konkateniere {len(segment_paths)} Segmente → {concatenated.name}"
        )

        (
            ffmpeg.input(concat_list_path, format="concat", safe=0)
            .output(concatenated.as_posix(), c="copy", movflags="+faststart")
            .overwrite_output()
            .run(quiet=not DEBUG_FFMPEG)
        )

        return concatenated

    except ffmpeg.Error as exc:
        error_msg = f"FFmpeg-Fehler bei Segment-Konkatenation: {exc}"
        logger.error(error_msg, exc_info=True)
        raise FFmpegError(error_msg) from exc
    except Exception as exc:
        error_msg = f"Fehler bei Segment-Konkatenation: {exc}"
        logger.error(error_msg, exc_info=True)
        raise RenderError(error_msg) from exc
    finally:
        # Cleanup Concat-Datei
        try:
            os.remove(concat_list_path)
            logger.debug(f"Concat-Datei gelöscht: {concat_list_path}")
        except OSError as exc:
            logger.debug(f"Konnte Concat-Datei nicht löschen: {concat_list_path} - {exc}")


def _apply_watermark(
    video_stream: Any,
    watermark_cfg: Optional[Dict[str, Any]],
    width: int,
) -> Any:
    """Appliziert Wasserzeichen-Overlay auf Video-Stream.

    Unterstützt:
    - Positionierung (top-left, top-right, bottom-left, bottom-right, center)
    - Absolute Breite oder relative Breite (% von Video)
    - Opacity/Transparenz
    - Skipping wenn Datei nicht existiert

    Args:
        video_stream: FFmpeg Video-Stream
        watermark_cfg: Config-Dict mit Keys:
            - path: Pfad zur Watermark-Datei (PNG/JPEG)
            - position: "top-left", "top-right", etc.
            - margin: Abstand vom Rand (Pixel)
            - width: Absolute Breite der Watermark
            - relative_width: Relative Breite (0.0-1.0)
            - opacity: 0.0-1.0 (0=transparent, 1=opaque)
        width: Video-Breite (für relative_width Berechnung)

    Returns:
        FFmpeg Stream mit Watermark oder unverändert wenn keine Config

    Logs:
        DEBUG: Watermark-Parameter
        WARNING: Datei nicht gefunden
    """
    if not watermark_cfg:
        return video_stream

    watermark_path = watermark_cfg.get("path")
    if not watermark_path:
        return video_stream

    path = Path(watermark_path)
    if not path.exists():
        logger.warning(f"Wasserzeichen nicht gefunden: {path} – übersprungen")
        return video_stream

    logger.debug(f"Appliziere Wasserzeichen: {path.name}")

    # Positionierung
    margin = int(watermark_cfg.get("margin", 40))
    position = watermark_cfg.get("position", "top-right")
    x_expr, y_expr = WATERMARK_POSITIONS.get(
        position, WATERMARK_POSITIONS["top-right"]
    )

    # Watermark laden und skalieren
    overlay = ffmpeg.input(path.as_posix())
    target_width = watermark_cfg.get("width")
    if isinstance(target_width, (int, float)) and target_width > 0:
        logger.debug(f"Watermark-Breite (absolut): {target_width}")
        overlay = overlay.filter("scale", int(target_width), -1)
    elif isinstance(watermark_cfg.get("relative_width"), (int, float)):
        relative = watermark_cfg["relative_width"]
        calc_width = int(width * relative)
        logger.debug(f"Watermark-Breite (relativ): {relative} → {calc_width}px")
        overlay = overlay.filter("scale", calc_width, -1)

    # Transparenz anwenden
    opacity = watermark_cfg.get("opacity", 1.0)
    if opacity < 1.0:
        logger.debug(f"Watermark-Opacity: {opacity}")
        overlay = overlay.filter("format", "rgba").filter(
            "colorchannelmixer", aa=opacity
        )

    # Overlay anwenden
    x = x_expr.format(margin=margin)
    y = y_expr.format(margin=margin)
    logger.debug(f"Watermark-Position: {position} (x={x}, y={y})")

    return ffmpeg.overlay(video_stream, overlay, x=x, y=y)


def _mix_background_audio(
    audio_stream: Any, music_cfg: Optional[Dict[str, Any]]
) -> Any:
    """Mischt Hintergrundmusik mit Original-Audio.

    Features:
    - Audio-Looping (Musik lädt automatisch neu)
    - Volume-Kontrolle für Musik
    - Auto-Ducking (Original-Audio wird leiser wenn Musik läuft)

    Args:
        audio_stream: FFmpeg Audio-Stream des Videos
        music_cfg: Config-Dict mit Keys:
            - path: Pfad zur Musik-Datei (MP3/WAV)
            - volume: Lautstärke der Musik (0.0-1.0)
            - ducking: Reduktion Original-Audio (0.0-1.0)
                     z.B. 0.8 = Original wird auf 80% reduziert

    Returns:
        FFmpeg Audio-Stream mit Musik gemischt, oder unverändert wenn keine Config

    Logs:
        DEBUG: Musik-Parameter
        WARNING: Datei nicht gefunden
    """
    if not music_cfg:
        return audio_stream

    music_path = music_cfg.get("path")
    if not music_path:
        return audio_stream

    path = Path(music_path)
    if not path.exists():
        logger.warning(f"Hintergrundmusik nicht gefunden: {path} – übersprungen")
        return audio_stream

    logger.debug(f"Mische Musik: {path.name}")

    # Musik laden mit Looping
    volume = float(music_cfg.get("volume", 0.1))
    music_stream = ffmpeg.input(
        path.as_posix(), stream_loop=-1
    ).audio.filter("volume", volume)

    logger.debug(f"Musik-Lautstärke: {volume}")

    # Auto-Ducking (Original-Audio leiser machen)
    ducking = music_cfg.get("ducking")
    if isinstance(ducking, (int, float)) and 0 < ducking < 1:
        logger.debug(f"Audio-Ducking: Original wird auf {ducking * 100}% reduziert")
        audio_stream = audio_stream.filter("volume", ducking)

    # Musik und Original-Audio mischen
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
    settings: Optional[Dict[str, Any]] = None,
) -> str:
    """Erstellt eine Video-Compilation mit Advanced-Effekten.

    Orchestriert kompletten Rendering-Prozess:
    1. Segment-Assembly (Intro + Clips + Outro)
    2. Segment-Normalisierung (Scaling, Padding, Audio)
    3. Konkatenation
    4. Template-Effekte (Watermark, Musik)
    5. Finale Encoding

    Args:
        video_paths: Iterable mit Pfaden zu Input-Videos
        output_path: Pfad zur Output-Videodatei
        vertical: True für 9:16 (Mobile), False für 16:9 (Desktop)
        fps: Frames per Second (Standard: 30)
        settings: Rendering-Settings Dictionary mit Keys:
            - render_vertical: Override für vertical parameter
            - render_preset: FFmpeg Encoding Preset (fast/medium/slow)
            - render_video_bitrate: Video Bitrate (z.B. "6000k")
            - render_audio_bitrate: Audio Bitrate (z.B. "192k")
            - render_padding_color: Padding-Farbe (z.B. "black")
            - render_intro_path: Optionaler Intro-Clip
            - render_outro_path: Optionaler Outro-Clip
            - render_watermark: Watermark-Konfiguration
            - render_background_music: Musik-Konfiguration
            - render_loudness: Loudness-Normalisierung
            - temp_folder: Temp-Verzeichnis

    Returns:
        Pfad zur Output-Videodatei

    Raises:
        RenderError: Bei kritischen Rendering-Fehlern
        ValueError: Wenn keine gültigen Videos zum Rendern

    Logs:
        INFO: Rendering-Status und Meilensteine
        DEBUG: Detail-Informationen für Debugging
        ERROR: Kritische Fehler mit Stack-Trace
    """
    try:
        # Initialisierung
        resolved_output = Path(output_path)
        resolved_output.parent.mkdir(parents=True, exist_ok=True)

        settings = settings or {}

        # Video-Format bestimmen
        target_width, target_height = VERTICAL_FORMAT if vertical else HORIZONTAL_FORMAT
        logger.info(
            f"Starte Video-Rendering: {target_width}x{target_height} @ {fps}fps "
            f"({'vertikal' if vertical else 'horizontal'})"
        )

        loudness_cfg = settings.get("render_loudness", {})

        # Phase 1: Segment-Assembly
        logger.debug("Phase 1: Segment-Assembly")
        raw_segments = _assemble_segments(video_paths, settings)
        if not raw_segments:
            raise ValueError(
                "Keine gültigen Videos zum Rendern übergeben "
                "(Clips nicht gefunden oder leer)"
            )

        logger.info(f"Phase 1 abgeschlossen: {len(raw_segments)} Segmente assembliert")

        # Phase 2: Segment-Normalisierung
        logger.debug("Phase 2: Segment-Normalisierung")
        temp_dir = Path(settings.get("temp_folder", "./temp"))
        prepared_segments: list[Path] = []
        concatenated: Optional[Path] = None

        for i, segment in enumerate(raw_segments, 1):
            logger.debug(f"Normalisiere Segment {i}/{len(raw_segments)}: {segment.name}")
            prepared = _prepare_segment(
                segment,
                temp_dir,
                target_width,
                target_height,
                fps,
                loudness_cfg,
                settings,
            )
            prepared_segments.append(prepared)

        logger.info(f"Phase 2 abgeschlossen: {len(prepared_segments)} Segmente normalisiert")

        try:
            # Phase 3: Konkatenation
            logger.debug("Phase 3: Segment-Konkatenation")
            concatenated = _concat_segments(prepared_segments, temp_dir)
            logger.info(f"Phase 3 abgeschlossen: Segmente konkateniert")

            # Phase 4: Template-Effekte und Finale Encoding
            logger.debug("Phase 4: Template-Effekte und Encoding")
            logger.info(f"Appliziere Template-Effekte und schreibe {resolved_output}")

            final_stream = ffmpeg.input(concatenated.as_posix())
            video_stream = final_stream.video
            audio_stream = _ensure_audio(final_stream, True)

            # Watermark anwenden
            video_stream = _apply_watermark(
                video_stream, settings.get("render_watermark"), target_width
            )

            # Musik mischen
            audio_stream = _mix_background_audio(
                audio_stream, settings.get("render_background_music")
            )

            # Final Loudness Normalisierung
            audio_stream = _loudnorm(audio_stream, loudness_cfg)

            # Output-Parameter
            output_args: Dict[str, Any] = {
                "preset": settings.get("render_preset", "medium"),
                "movflags": "+faststart",
                "pix_fmt": "yuv420p",
                "r": fps,
                "ac": 2,
                "b:v": settings.get("render_video_bitrate", "6000k"),
                "b:a": settings.get("render_audio_bitrate", "192k"),
            }

            logger.debug(f"Final Output-Args: {output_args}")

            (
                ffmpeg.output(
                    video_stream, audio_stream, resolved_output.as_posix(), **output_args
                )
                .overwrite_output()
                .run(quiet=not DEBUG_FFMPEG)
            )

            logger.info(f"Phase 4 abgeschlossen: Output gespeichert in {resolved_output}")
            logger.info(f"Rendering erfolgreich abgeschlossen: {resolved_output}")

            return resolved_output.as_posix()

        finally:
            # Cleanup temporäre Dateien
            logger.debug("Cleanup temporärer Dateien")
            for path in prepared_segments:
                try:
                    path.unlink(missing_ok=True)
                except OSError as exc:
                    logger.debug(f"Konnte temporäre Datei nicht löschen: {path} - {exc}")

            if concatenated is not None:
                try:
                    concatenated.unlink(missing_ok=True)
                except OSError as exc:
                    logger.debug(
                        f"Konnte Concatenated-Datei nicht löschen: {concatenated} - {exc}"
                    )

    except (RenderError, FFmpegError):
        raise
    except ValueError:
        raise
    except Exception as exc:
        error_msg = f"Unerwarteter Fehler beim Video-Rendering: {exc}"
        logger.error(error_msg, exc_info=True)
        raise RenderError(error_msg) from exc