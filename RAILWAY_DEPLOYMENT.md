# YouTube Downloader & QR Generator - Railway Deployment

## 📋 Archivos a subir a Railway

Estos son los archivos **esenciales** que necesitas subir:

```
├── app_web.py              ✅ Servidor Flask (OBLIGATORIO)
├── requirements.txt        ✅ Dependencias Python (OBLIGATORIO)
├── Procfile               ✅ Configuración de Railway (OBLIGATORIO)
├── runtime.txt            ✅ Versión de Python (OBLIGATORIO)
└── templates/
    └── index.html         ✅ Interfaz web (OBLIGATORIO)
```

## 🚀 Pasos para desplegar en Railway

### 1. Opción A: Desde GitHub (Recomendado)

1. **Sube tu proyecto a GitHub**:
   ```bash
   git init
   git add .
   git commit -m "Initial commit"
   git remote add origin https://github.com/TU_USUARIO/ytdownloader.git
   git push -u origin main
   ```

2. **Conecta Railway a GitHub**:
   - Ve a [railway.app](https://railway.app)
   - Crea una cuenta (o inicia sesión)
   - Haz clic en "New Project"
   - Selecciona "Deploy from GitHub"
   - Autoriza y selecciona tu repositorio `ytdownloader`
   - Railway detectará automáticamente `Procfile` y `requirements.txt`
   - Haz clic en "Deploy"

### 2. Opción B: CLI de Railway (Alternativa)

```bash
# 1. Instala Railway CLI
npm install -g @railway/cli

# 2. Inicia sesión
railway login

# 3. Crea proyecto en Railway
cd "/Users/jhonatanmejiamendoza/Documents/Docs Pancri/proyectos/YTDownloader"
railway init

# 4. Deploya
railway up
```

## ⚙️ Variables de entorno (Opcional)

Si necesitas variables, en Railway Dashboard:
- Ve a "Settings" → "Environment"
- Añade variables como `PORT` (se asigna automáticamente)

## 🔗 Acceso a tu app

Una vez desplegada, Railway te dará una URL como:
```
https://tu-app-xxxxx.railway.app
```

## ⚠️ Limitaciones en Railway (versión gratuita)

- **Almacenamiento limitado**: Los archivos se borran al reiniciar
- **Timeout**: Máximo 2-3 minutos por descarga (yt-dlp puede ser lento)
- **RAM limitada**: ~512MB

## 💡 Mejora: Almacenamiento en la nube

Para archivos permanentes, agrega S3 (AWS):
- Instala: `pip install boto3`
- Configura credenciales en variables de entorno
- Modifica `app_web.py` para guardar en S3

## 📦 Estructura del repositorio Git

```
ytdownloader/
├── app_web.py
├── requirements.txt
├── Procfile
├── runtime.txt
├── templates/
│   └── index.html
├── ytDownloader.py         (opcional, referencia)
├── urlQr.py               (opcional, referencia)
└── main.py                (opcional, referencia)
```

## ✅ Checklist final antes de desplegar

- [x] `Procfile` existe y tiene: `web: python app_web.py`
- [x] `runtime.txt` existe con versión Python
- [x] `requirements.txt` tiene todas las dependencias
- [x] `app_web.py` usa `PORT = os.environ.get('PORT', 5000)`
- [x] Carpeta `templates/` con `index.html` existe
- [x] Todo está en un repositorio Git
