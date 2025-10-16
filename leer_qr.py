import cv2
import requests
import json

API_ASISTENCIAS = "http://127.0.0.1:8000/api/asistencias/"

def obtener_ultimo_registro(empleado_id):
    try:
        url = f"{API_ASISTENCIAS}?empleado={empleado_id}"
        response = requests.get(url)
        if response.status_code == 200:
            data = response.json()
            if data:
                return data[-1]  # último registro
        return None
    except Exception as e:
        print("⚠️ No se pudo consultar la API:", e)
        return None

def enviar_asistencia(empleado_id):
    ultimo = obtener_ultimo_registro(empleado_id)

    if ultimo and ultimo.get("tipo") == "entrada":
        tipo = "salida"
    else:
        tipo = "entrada"

    payload = {
        "empleado": empleado_id,
        "tipo": tipo
    }
    headers = {"Content-Type": "application/json"}

    try:
        response = requests.post(API_ASISTENCIAS, data=json.dumps(payload), headers=headers)
        if response.status_code == 201:
            print(f"✅ {tipo.capitalize()} registrada:", response.json())
        else:
            print("❌ Error al registrar asistencia:", response.text)
    except Exception as e:
        print("⚠️ No se pudo conectar con la API:", e)

def leer_qr_opencv():
    cap = cv2.VideoCapture(0)
    detector = cv2.QRCodeDetector()

    print("📷 Escaneando QR...")

    while True:
        ret, frame = cap.read()
        if not ret:
            break

        data, bbox, _ = detector.detectAndDecode(frame)
        if data:
            print(f"✅ QR detectado: {data}")

            try:
                empleado = json.loads(data)  # El QR debe ser un JSON válido
                enviar_asistencia(empleado["id"])
            except Exception as e:
                print("⚠️ El QR no tiene un formato válido:", e)

            if bbox is not None and len(bbox) > 0:
                for i in range(len(bbox)):
                    pt1 = tuple(map(int, bbox[i][0]))
                    pt2 = tuple(map(int, bbox[(i+1) % len(bbox)][0]))
                    cv2.line(frame, pt1, pt2, (0, 255, 0), 2)

            cv2.putText(frame, data, (20, 50),
                        cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 255, 0), 2)

        cv2.imshow("Escanear QR", frame)

        if cv2.waitKey(1) & 0xFF == ord("q"):
            break

    cap.release()
    cv2.destroyAllWindows()

if __name__ == "__main__":
    leer_qr_opencv()
