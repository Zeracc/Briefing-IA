from PIL import Image
if not hasattr(Image, 'ANTIALIAS'):  # recria o atributo para compatibilidade
    Image.ANTIALIAS = Image.Resampling.LANCZOS


import os
from moviepy.editor import VideoFileClip


def create_video_proxy(video_path, output_path, resolution=(640, 360), bitrate="800k"):
    """Gera um proxy do vídeo (reduz resolução e bitrate)."""
    print("🎞️ Gerando proxy...")
    clip = VideoFileClip(video_path)
    clip_resized = clip.resize(newsize=resolution)
    clip_resized.write_videofile(
        output_path,
        bitrate=bitrate,
        codec="libx264",
        audio_codec="aac",
        preset="ultrafast",
        threads=4,
        verbose=False,
        logger=None
    )
    clip.close()
    clip_resized.close()
    print(f"✅ Proxy salvo em: {output_path}")


def extract_frames(video_path, output_folder="frames", interval_minutes=1):
    """Extrai 1 frame por minuto do vídeo."""
    if not os.path.exists(video_path):
        print("❌ Vídeo não encontrado:", video_path)
        return

    video_name = os.path.splitext(os.path.basename(video_path))[0]
    output_dir = os.path.join(output_folder, video_name)
    os.makedirs(output_dir, exist_ok=True)

    clip = VideoFileClip(video_path)
    duration = clip.duration
    interval = interval_minutes * 60

    print(f"🎬 Processando vídeo: {video_name}")
    print(f"⏱ Duração total: {duration:.2f}s")
    print(f"📸 Captura a cada {interval_minutes} min")

    t = 0
    frame_count = 0
    while t < duration:
        frame_path = os.path.join(output_dir, f"frame_{frame_count:03d}.jpg")
        clip.save_frame(frame_path, t)
        print(f"✅ Frame {frame_count} salvo ({t:.2f}s)")
        frame_count += 1
        t += interval

    clip.close()
    print(f"✨ Extração concluída! Total: {frame_count} frames")


if __name__ == "__main__":
    caminho_video = "meu_video.mp4"
    proxy_path = "proxy_meu_video.mp4"

    # 1️⃣ Gera o proxy primeiro
    create_video_proxy(caminho_video, proxy_path,
                       resolution=(640, 360), bitrate="800k")

    # 2️⃣ Depois extrai os frames do proxy (mais leve)
    extract_frames(proxy_path, interval_minutes=1)
