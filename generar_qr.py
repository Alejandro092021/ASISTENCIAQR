import qrcode

def generar_qr(id_empleado, nombre):
    data = {
        "id": id_empleado,
        "nombre": nombre
    }
    qr = qrcode.make(data)
    qr.save(f"{nombre}_{id_empleado}.png")
    print(f"✅ QR generado para {nombre} - Archivo: {nombre}_{id_empleado}.png")

# Ejemplo de uso
if __name__ == "__main__":
    generar_qr(2, "Alejandro_Figueroa")
