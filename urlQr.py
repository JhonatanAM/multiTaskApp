import os
import qrcode


def convertirUrlaQr(url, name):
    outdir = 'qrs'
    os.makedirs(outdir, exist_ok=True)

    # Generar el código QR
    img = qrcode.make(url)
    img.save(os.path.join(outdir, f"{name}.png"))

if __name__ == '__main__':
    url = input("Introduce la URL: ")
    name = input("Introduce el nombre del archivo QR (sin extensión): ")
    convertirUrlaQr(url, name)
    print("Código QR generado y guardado correctamente.")