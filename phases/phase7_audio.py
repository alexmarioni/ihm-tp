"""
Fase 7: Genera narración con edge-tts (gratis) y la mezcla con el video silencioso.
Salida: output/video_final.mp4
"""

import asyncio
import os
import subprocess
from pathlib import Path

import edge_tts

from utils.checkpoint import load_checkpoint

TTS_VOICE = os.getenv("TTS_VOICE", "es-ES-AlvaroNeural")
TTS_RATE = os.getenv("TTS_RATE", "-10%")


def build_narration_script(storyboard: dict) -> str:
    parts = []
    for escena in storyboard["escenas"]:
        texto = escena.get("texto_narracion", "")
        if texto:
            parts.append(texto)
    return "... ".join(parts)


async def _generate_tts(script: str, output_path: str) -> None:
    communicate = edge_tts.Communicate(
        text=script,
        voice=TTS_VOICE,
        rate=TTS_RATE,
    )
    await communicate.save(output_path)


def generate_tts(script: str, output_path: str) -> None:
    asyncio.run(_generate_tts(script, output_path))


def merge_audio_video(video_path: str, audio_path: str, output_path: str, total_duration: int) -> None:
    fade_out_start = max(0, total_duration - 0.8)

    cmd = [
        "ffmpeg", "-y",
        "-i", video_path,
        "-i", audio_path,
        "-c:v", "copy",
        "-c:a", "aac",
        "-b:a", "128k",
        "-af", f"afade=t=in:st=0:d=0.4,afade=t=out:st={fade_out_start}:d=0.8",
        "-map", "0:v:0",
        "-map", "1:a:0",
        "-shortest",
        output_path,
    ]
    subprocess.run(cmd, check=True, capture_output=True)


def run(pdf_path: str, output_dir: str) -> dict:
    storyboard = load_checkpoint(os.path.join(output_dir, "phase4_storyboard.json"))
    if storyboard is None:
        raise RuntimeError("Fase 4 debe completarse primero.")

    silent_video = os.path.join(output_dir, "video_silent.mp4")
    if not os.path.exists(silent_video):
        raise RuntimeError("Fase 6 debe completarse primero (video_silent.mp4 no encontrado).")

    audio_dir = os.path.join(output_dir, "phase7_audio")
    os.makedirs(audio_dir, exist_ok=True)

    narration_path = os.path.join(audio_dir, "narration.mp3")
    final_video = os.path.join(output_dir, "video_final.mp4")

    if os.path.exists(final_video):
        print("  [checkpoint] video_final.mp4 ya existe, saltando fase 7.")
        return {"video_final": final_video}

    script = build_narration_script(storyboard)
    print(f"  Narración: '{script}'")

    if not os.path.exists(narration_path):
        print(f"  Generando TTS con edge-tts (voz: {TTS_VOICE})...")
        generate_tts(script, narration_path)
        print(f"  Audio guardado: {narration_path}")
    else:
        print("  [checkpoint] narration.mp3 ya existe.")

    total_duration = storyboard.get("duracion_total", 12)
    print("  Mezclando audio + video...")
    merge_audio_video(silent_video, narration_path, final_video, total_duration)
    print(f"  Video final: {final_video}")

    return {"video_final": final_video}
