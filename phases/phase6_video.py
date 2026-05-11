"""
Fase 6: Composición de video — Ken Burns (FFmpeg) + text overlay (Pillow) → video_silent.mp4
"""

import os
import subprocess
import tempfile
from pathlib import Path

from utils.checkpoint import load_checkpoint
from utils.text_overlay import render_text_overlay

VIDEO_WIDTH = int(os.getenv("VIDEO_WIDTH", "1080"))
VIDEO_HEIGHT = int(os.getenv("VIDEO_HEIGHT", "1920"))
FPS = int(os.getenv("VIDEO_FPS", "24"))

FFMPEG = "ffmpeg"


def build_ken_burns_filter(escena: dict) -> str:
    kb = escena.get("movimiento_ken_burns", {})
    duration = escena["duracion"]
    total_frames = duration * FPS

    tipo = kb.get("tipo", "zoom_in")
    z_start = kb.get("zoom_inicio", 1.0)
    z_end = kb.get("zoom_fin", 1.12)

    if tipo == "zoom_in":
        zoom_expr = f"{z_start}+({z_end}-{z_start})*on/{total_frames}"
        x_expr = "iw/2-(iw/zoom/2)"
        y_expr = "ih/2-(ih/zoom/2)"
    elif tipo == "zoom_out":
        zoom_expr = f"{z_end}+({z_start}-{z_end})*(1-on/{total_frames})"
        x_expr = "iw/2-(iw/zoom/2)"
        y_expr = "ih/2-(ih/zoom/2)"
    elif tipo == "pan_left":
        zoom_expr = f"{z_start}+({z_end}-{z_start})*on/{total_frames}"
        shift = 0.06
        x_expr = f"iw/2-(iw/zoom/2)+{shift}*iw*on/{total_frames}"
        y_expr = "ih/2-(ih/zoom/2)"
    elif tipo == "pan_right":
        zoom_expr = f"{z_start}+({z_end}-{z_start})*on/{total_frames}"
        shift = 0.06
        x_expr = f"iw/2-(iw/zoom/2)-{shift}*iw*on/{total_frames}"
        y_expr = "ih/2-(ih/zoom/2)"
    else:
        zoom_expr = f"{z_start}+({z_end}-{z_start})*on/{total_frames}"
        x_expr = "iw/2-(iw/zoom/2)"
        y_expr = "ih/2-(ih/zoom/2)"

    fade_dur = min(0.25, duration * 0.1)

    vf = (
        f"scale={VIDEO_WIDTH}:{VIDEO_HEIGHT}:force_original_aspect_ratio=increase,"
        f"crop={VIDEO_WIDTH}:{VIDEO_HEIGHT},"
        f"zoompan="
        f"z='{zoom_expr}':"
        f"x='{x_expr}':"
        f"y='{y_expr}':"
        f"d={total_frames}:"
        f"s={VIDEO_WIDTH}x{VIDEO_HEIGHT}:"
        f"fps={FPS},"
        f"fade=t=in:st=0:d={fade_dur},"
        f"fade=t=out:st={duration - fade_dur}:d={fade_dur},"
        f"format=yuv420p"
    )
    return vf


def generate_scene_clip(escena: dict, image_path: str, output_path: str) -> None:
    vf_filter = build_ken_burns_filter(escena)
    duration = escena["duracion"]

    cmd = [
        FFMPEG, "-y",
        "-loop", "1",
        "-i", image_path,
        "-vf", vf_filter,
        "-t", str(duration),
        "-c:v", "libx264",
        "-pix_fmt", "yuv420p",
        "-an",
        output_path,
    ]
    subprocess.run(cmd, check=True, capture_output=True)


def overlay_text_on_clip(clip_path: str, texto: str, output_path: str) -> None:
    """Genera overlay PNG con Pillow y lo compone sobre el clip con FFmpeg."""
    overlay_img = render_text_overlay(texto, width=VIDEO_WIDTH, height=VIDEO_HEIGHT)

    with tempfile.NamedTemporaryFile(suffix=".png", delete=False) as tmp:
        overlay_img.save(tmp.name, format="PNG")
        tmp_path = tmp.name

    try:
        cmd = [
            FFMPEG, "-y",
            "-i", clip_path,
            "-i", tmp_path,
            "-filter_complex", "[0:v][1:v]overlay=0:0",
            "-c:v", "libx264",
            "-pix_fmt", "yuv420p",
            "-an",
            output_path,
        ]
        subprocess.run(cmd, check=True, capture_output=True)
    finally:
        os.unlink(tmp_path)


def compose_video(storyboard: dict, images_dir: str, segments_dir: str, output_path: str) -> None:
    os.makedirs(segments_dir, exist_ok=True)
    segment_paths = []

    for escena in storyboard["escenas"]:
        n = escena["orden"]
        image_path = os.path.join(images_dir, f"scene{n}_img0.png")

        if not os.path.exists(image_path):
            raise FileNotFoundError(f"Imagen no encontrada: {image_path}")

        raw_clip = os.path.join(segments_dir, f"scene{n}_raw.mp4")
        final_clip = os.path.join(segments_dir, f"scene{n}.mp4")

        print(f"  Escena {n} ({escena['nombre']}): aplicando Ken Burns...")
        generate_scene_clip(escena, image_path, raw_clip)

        texto = escena.get("texto_pantalla")
        if texto:
            print(f"  Escena {n}: añadiendo texto '{texto}'...")
            overlay_text_on_clip(raw_clip, texto, final_clip)
            os.unlink(raw_clip)
        else:
            os.rename(raw_clip, final_clip)

        segment_paths.append(final_clip)

    # Concatenar escenas
    clips_file = os.path.join(segments_dir, "clips.txt")
    with open(clips_file, "w", encoding="utf-8") as f:
        for path in segment_paths:
            posix = Path(path).resolve().as_posix()
            f.write(f"file '{posix}'\n")

    print("  Uniendo escenas...")
    cmd = [
        FFMPEG, "-y",
        "-f", "concat",
        "-safe", "0",
        "-i", clips_file,
        "-c", "copy",
        output_path,
    ]
    subprocess.run(cmd, check=True, capture_output=True)
    print(f"  Video silencioso guardado: {output_path}")


def run(pdf_path: str, output_dir: str) -> dict:
    storyboard = load_checkpoint(os.path.join(output_dir, "phase4_storyboard.json"))
    if storyboard is None:
        raise RuntimeError("Fase 4 debe completarse primero.")

    images_dir = os.path.join(output_dir, "phase5_images")
    segments_dir = os.path.join(output_dir, "phase6_segments")
    silent_video = os.path.join(output_dir, "video_silent.mp4")

    if os.path.exists(silent_video):
        print("  [checkpoint] video_silent.mp4 ya existe, saltando fase 6.")
        return {"video_silent": silent_video}

    compose_video(storyboard, images_dir, segments_dir, silent_video)
    return {"video_silent": silent_video}
