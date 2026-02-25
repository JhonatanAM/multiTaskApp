import tkinter as tk
from tkinter import ttk, simpledialog, messagebox
import os
import yt_dlp
import qrcode
from tkinter import scrolledtext

class YouTubeDownloaderApp:
    def __init__(self, root):
        self.root = root
        self.root.title("YouTube Downloader & QR Generator")
        self.root.geometry("500x400")
        self.root.resizable(False, False)
        
        # Frame principal
        main_frame = ttk.Frame(root, padding="20")
        main_frame.pack(fill=tk.BOTH, expand=True)
        
        # Título
        title = ttk.Label(main_frame, text="Selecciona una opción", font=("Arial", 18, "bold"))
        title.pack(pady=20)
        
        # Botón descargar MP3
        btn_mp3 = ttk.Button(
            main_frame,
            text="📥 Descargar MP3 de YouTube",
            command=self.descargar_mp3_dialog
        )
        btn_mp3.pack(pady=10, fill=tk.X, ipady=10)
        
        # Botón generar QR
        btn_qr = ttk.Button(
            main_frame,
            text="📱 Generar Código QR",
            command=self.generar_qr_dialog
        )
        btn_qr.pack(pady=10, fill=tk.X, ipady=10)
        
        # Area de logs
        ttk.Label(main_frame, text="Historial:", font=("Arial", 10)).pack(pady=(20, 5))
        self.log_text = scrolledtext.ScrolledText(main_frame, height=8, width=50, state=tk.DISABLED)
        self.log_text.pack(fill=tk.BOTH, expand=True)
        
    def log(self, mensaje):
        """Añade mensaje al área de logs"""
        self.log_text.config(state=tk.NORMAL)
        self.log_text.insert(tk.END, mensaje + "\n")
        self.log_text.see(tk.END)
        self.log_text.config(state=tk.DISABLED)
    
    def descargar_mp3_dialog(self):
        """Diálogo para descargar MP3"""
        url = simpledialog.askstring("Descargar MP3", "Introduce la URL de YouTube:")
        if url:
            self.log(f"⏳ Descargando: {url}")
            try:
                self.descargar_youtube_mp3(url)
                self.log("✅ MP3 descargado correctamente en la carpeta 'mp3/'")
                messagebox.showinfo("Éxito", "MP3 descargado correctamente.\nGuardado en: mp3/")
            except Exception as e:
                error_msg = f"❌ Error: {str(e)}"
                self.log(error_msg)
                messagebox.showerror("Error", f"Error al descargar:\n{str(e)}")
    
    def generar_qr_dialog(self):
        """Diálogo para generar QR"""
        url = simpledialog.askstring("Generar QR", "Introduce la URL:")
        if url:
            name = simpledialog.askstring("Generar QR", "Nombre del archivo QR (sin extensión):")
            if name:
                self.log(f"⏳ Generando QR para: {url}")
                try:
                    self.convertir_url_a_qr(url, name)
                    self.log(f"✅ QR generado: {name}.png")
                    messagebox.showinfo("Éxito", f"QR generado correctamente.\nGuardado en: qrs/{name}.png")
                except Exception as e:
                    error_msg = f"❌ Error: {str(e)}"
                    self.log(error_msg)
                    messagebox.showerror("Error", f"Error al generar QR:\n{str(e)}")
    
    def descargar_youtube_mp3(self, url):
        """Descarga MP3 de YouTube"""
        outdir = 'mp3'
        os.makedirs(outdir, exist_ok=True)
        
        ydl_opts = {
            'format': 'bestaudio/best',
            'postprocessors': [{
                'key': 'FFmpegExtractAudio',
                'preferredcodec': 'mp3',
                'preferredquality': '192',
            }],
            'outtmpl': os.path.join(outdir, '%(title)s.%(ext)s'),
            'quiet': False,
            'no_warnings': False,
        }
        
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            ydl.download([url])
    
    def convertir_url_a_qr(self, url, name):
        """Convierte URL a código QR"""
        outdir = 'qrs'
        os.makedirs(outdir, exist_ok=True)
        
        img = qrcode.make(url)
        img.save(os.path.join(outdir, f"{name}.png"))

if __name__ == '__main__':
    root = tk.Tk()
    app = YouTubeDownloaderApp(root)
    root.mainloop()
