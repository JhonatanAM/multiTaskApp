from flask import Flask, render_template, request, send_file, jsonify
import os
import yt_dlp
import qrcode
from io import BytesIO
from pathlib import Path
import threading
import uuid
from werkzeug.utils import secure_filename
import functools
import shutil
import stat
import tarfile
import urllib.request
import logging

# Authentication for admin actions (upload/delete persistent cookies)
API_KEY = os.environ.get('APP_API_KEY')

def require_api_key(fn):
    @functools.wraps(fn)
    def wrapper(*args, **kwargs):
        if not API_KEY:
            # If no API key set, allow (developer convenience)
            return fn(*args, **kwargs)
        auth = request.headers.get('Authorization', '')
        if not auth.startswith('Bearer '):
            return jsonify({'error': 'Unauthorized'}), 401
        token = auth.split(' ', 1)[1]
        if token != API_KEY:
            return jsonify({'error': 'Unauthorized'}), 401
        return fn(*args, **kwargs)
    return wrapper

app = Flask(__name__)

# Crear carpetas si no existen
os.makedirs('mp3', exist_ok=True)
os.makedirs('qrs', exist_ok=True)


def ensure_ffmpeg():
    """Ensure ffmpeg and ffprobe are available.
    Returns a path to ffmpeg binaries directory (string) or None to use system ffmpeg.
    """
    # 1) system
    if shutil.which('ffmpeg') and shutil.which('ffprobe'):
        logging.info('ffmpeg found on PATH')
        return None

    # 2) env var
    env_path = os.environ.get('FFMPEG_PATH')
    if env_path:
        ff = os.path.join(env_path, 'ffmpeg')
        fp = os.path.join(env_path, 'ffprobe')
        if os.path.exists(ff) and os.path.exists(fp):
            logging.info('Using ffmpeg from FFMPEG_PATH')
            return env_path

    # 3) local bin
    local_ff = os.path.join('bin', 'ffmpeg')
    local_fp = os.path.join('bin', 'ffprobe')
    if os.path.exists(local_ff) and os.path.exists(local_fp):
        logging.info('Using local ./bin/ffmpeg')
        return os.path.abspath('bin')

    # 4) attempt download (best-effort for Linux x86_64)
    try:
        os.makedirs('bin', exist_ok=True)
        url = 'https://johnvansickle.com/ffmpeg/releases/ffmpeg-release-amd64-static.tar.xz'
        archive = os.path.join('bin', 'ffmpeg-static.tar.xz')
        logging.info('Attempting to download ffmpeg static build...')
        urllib.request.urlretrieve(url, archive)
        with tarfile.open(archive, 'r:xz') as tf:
            members = [m for m in tf.getmembers() if m.name.endswith('/ffmpeg') or m.name.endswith('/ffprobe')]
            for m in members:
                m.name = os.path.basename(m.name)
                tf.extract(m, path='bin')

        # make executables
        for p in ('ffmpeg', 'ffprobe'):
            path = os.path.join('bin', p)
            if os.path.exists(path):
                st = os.stat(path)
                os.chmod(path, st.st_mode | stat.S_IEXEC)

        if os.path.exists(local_ff) and os.path.exists(local_fp):
            logging.info('ffmpeg downloaded to ./bin')
            return os.path.abspath('bin')
    except Exception as e:
        logging.warning(f'Could not auto-install ffmpeg: {e}')

    logging.error('ffmpeg not found')
    return None

@app.route('/')
def index():
    """Página principal"""
    return render_template('index.html')

@app.route('/descargar-mp3', methods=['POST'])
def descargar_mp3():
    """Endpoint para descargar MP3"""
    try:
        # Accept either JSON (no cookies) or multipart/form-data with an optional cookies file
        url = None
        cookies_path = None
        if request.is_json:
            url = request.json.get('url')
        else:
            # form-data: url in form, optional file in 'cookies'
            url = request.form.get('url')
            cookies_file = request.files.get('cookies')
            if cookies_file:
                cookies_dir = 'cookies'
                os.makedirs(cookies_dir, exist_ok=True)
                filename = secure_filename(cookies_file.filename) or f"cookies_{uuid.uuid4().hex}.txt"
                cookies_path = os.path.join(cookies_dir, f"{uuid.uuid4().hex}_{filename}")
                cookies_file.save(cookies_path)

        if not url:
            return jsonify({'error': 'URL no proporcionada'}), 400

        outdir = 'mp3'
        os.makedirs(outdir, exist_ok=True)

        # Ensure ffmpeg is available (system, env or downloaded into ./bin)
        ffmpeg_dir = ensure_ffmpeg()

        ydl_opts = {
            'format': 'bestaudio/best',
            'postprocessors': [{
                'key': 'FFmpegExtractAudio',
                'preferredcodec': 'mp3',
                'preferredquality': '192',
            }],
            'outtmpl': os.path.join(outdir, '%(title)s.%(ext)s'),
            'quiet': True,
            'no_warnings': True,
        }

        # If ensure_ffmpeg returned a dir (not None), point yt-dlp to it
        if ffmpeg_dir:
            # yt-dlp option is 'ffmpeg_location' to point to ffmpeg binary directory
            ydl_opts['ffmpeg_location'] = ffmpeg_dir

        # If a cookies file was uploaded, tell yt-dlp to use it
        if cookies_path:
            ydl_opts['cookiefile'] = cookies_path
        else:
            # If there is a persistent cookies file uploaded by admin, use it
            persistent = None
            cookies_dir = 'cookies'
            if os.path.exists(cookies_dir):
                for f in os.listdir(cookies_dir):
                    if f.startswith('persistent_'):
                        persistent = os.path.join(cookies_dir, f)
                        break
            if persistent:
                ydl_opts['cookiefile'] = persistent

        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(url, download=True)
            filename = ydl.prepare_filename(info)
            # Cambiar extensión a .mp3
            mp3_filename = os.path.splitext(filename)[0] + '.mp3'

        # Clean up temporary cookies file
        try:
            if cookies_path and os.path.exists(cookies_path):
                os.remove(cookies_path)
        except Exception:
            pass

        return jsonify({'success': True, 'mensaje': 'MP3 descargado', 'archivo': os.path.basename(mp3_filename)})
    
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/generar-qr', methods=['POST'])
def generar_qr():
    """Endpoint para generar QR y descargar"""
    try:
        data = request.json
        url = data.get('url')
        name = data.get('name', 'qr')
        
        if not url:
            return jsonify({'error': 'URL no proporcionada'}), 400
        
        # Generar QR en memoria
        qr = qrcode.make(url)
        img_io = BytesIO()
        qr.save(img_io, 'PNG')
        img_io.seek(0)
        
        # También guardar en servidor
        outdir = 'qrs'
        os.makedirs(outdir, exist_ok=True)
        qr.save(os.path.join(outdir, f"{name}.png"))
        
        return send_file(img_io, mimetype='image/png', as_attachment=True, download_name=f'{name}.png')
    
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@app.route('/admin/upload-cookies', methods=['POST'])
@require_api_key
def admin_upload_cookies():
    """Upload a persistent cookies.txt (admin only)."""
    try:
        cookies_file = request.files.get('cookies')
        if not cookies_file:
            return jsonify({'error': 'No file provided'}), 400
        cookies_dir = 'cookies'
        os.makedirs(cookies_dir, exist_ok=True)
        filename = secure_filename(cookies_file.filename) or 'cookies.txt'
        dest = os.path.join(cookies_dir, 'persistent_' + filename)
        cookies_file.save(dest)
        return jsonify({'success': True, 'path': dest})
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@app.route('/admin/delete-cookies', methods=['POST'])
@require_api_key
def admin_delete_cookies():
    """Delete the persistent cookies file (admin only)."""
    try:
        cookies_dir = 'cookies'
        if not os.path.exists(cookies_dir):
            return jsonify({'success': True, 'deleted': False, 'reason': 'no cookies directory'})
        deleted = []
        for f in os.listdir(cookies_dir):
            if f.startswith('persistent_'):
                path = os.path.join(cookies_dir, f)
                os.remove(path)
                deleted.append(f)
        return jsonify({'success': True, 'deleted': deleted})
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/descargar-qr-archivo/<name>')
def descargar_qr_archivo(name):
    """Descarga QR generado previamente"""
    try:
        filepath = os.path.join('qrs', f"{name}.png")
        if os.path.exists(filepath):
            return send_file(filepath, mimetype='image/png', as_attachment=True, download_name=f'{name}.png')
        return jsonify({'error': 'Archivo no encontrado'}), 404
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/descargar-mp3-archivo/<filename>')
def descargar_mp3_archivo(filename):
    """Descarga MP3 generado previamente"""
    try:
        filepath = os.path.join('mp3', filename)
        if os.path.exists(filepath):
            return send_file(filepath, mimetype='audio/mpeg', as_attachment=True, download_name=filename)
        return jsonify({'error': 'Archivo no encontrado'}), 404
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/listar-mp3')
def listar_mp3():
    """Lista los MP3 descargados"""
    try:
        archivos = os.listdir('mp3') if os.path.exists('mp3') else []
        return jsonify({'archivos': archivos})
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/listar-qr')
def listar_qr():
    """Lista los QR generados"""
    try:
        archivos = os.listdir('qrs') if os.path.exists('qrs') else []
        return jsonify({'archivos': archivos})
    except Exception as e:
        return jsonify({'error': str(e)}), 500

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    app.run(debug=False, host='0.0.0.0', port=port)
