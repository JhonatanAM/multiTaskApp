import os
import yt_dlp

def descargar_youtube_mp3(url):
    outdir = 'mp3'
    os.makedirs(outdir, exist_ok=True)

    ydl_opts = {
        'format': 'bestaudio/best',
        'postprocessors': [{
            'key': 'FFmpegExtractAudio',
            'preferredcodec': 'mp3',
            'preferredquality': '192',
        }],
        'outtmpl': os.path.join(outdir, '%(title)s.%(ext)s'), # Guarda en la carpeta mp3/
    }

    try:
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            ydl.download([url])
    except Exception as e:
        print(f"Error durante la descarga: {e}")

# Uso
if __name__ == '__main__':
    url_video = input("Introduce la URL de YouTube: ")
    descargar_youtube_mp3(url_video)
    print("Descarga y conversión completada.")
