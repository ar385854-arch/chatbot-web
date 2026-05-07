from flask import Flask, request, jsonify, send_file
from flask_cors import CORS
from openai import OpenAI
import csv
import os
from datetime import datetime

app = Flask(__name__)
CORS(app)

client = OpenAI()

RESERVAS_FILE = "citas.csv"

historial = [
    {
        "role": "system",
        "content": """
Eres un asistente profesional para gestionar citas en consultas, clínicas, dentistas, psicólogos y otros negocios de servicios.

Tu trabajo es recoger solicitudes de cita de forma clara y amable.

Datos a recoger:
- Nombre
- Motivo de la cita o servicio que necesita
- Día preferido
- Hora preferida
- Teléfono de contacto

NO preguntes cuántas personas son.
NO hables de restaurante.
NO digas reserva de mesa.
NO digas que el restaurante revisará disponibilidad.

Cuando tengas todos los datos, responde exactamente con este formato:

Perfecto, he tomado tu solicitud de cita.

Nombre: ...
Motivo: ...
Día: ...
Hora: ...
Teléfono: ...

El negocio revisará disponibilidad y te contactará en breve para confirmarla.

Sé breve, amable y profesional.
"""
    }
]


def guardar_cita(texto):
    if "Perfecto, he tomado tu solicitud de cita." not in texto:
        return

    existe = os.path.exists(RESERVAS_FILE)

    with open(RESERVAS_FILE, "a", newline="", encoding="utf-8") as archivo:
        writer = csv.writer(archivo)

        if not existe:
            writer.writerow(["fecha_registro", "estado", "texto"])

        writer.writerow([
            datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            "pendiente",
            texto
        ])


@app.route("/")
def home():
    return send_file("index.html")


@app.route("/chat", methods=["POST"])
def chat():
    data = request.get_json()
    mensaje = data.get("message", "")

    historial.append({"role": "user", "content": mensaje})

    respuesta = client.chat.completions.create(
        model="gpt-4o-mini",
        messages=historial
    )

    reply = respuesta.choices[0].message.content

    historial.append({"role": "assistant", "content": reply})

    guardar_cita(reply)

    return jsonify({"reply": reply})


@app.route("/reservas")
def ver_reservas():
    if not os.path.exists(RESERVAS_FILE):
        return "<h1>Citas recibidas</h1><p>No hay citas todavía.</p>"

    html = """
    <h1>Citas recibidas</h1>
    <style>
      body { font-family: Arial; padding: 30px; }
      .cita { border: 1px solid #ccc; padding: 15px; margin-bottom: 15px; border-radius: 10px; }
      .pendiente { color: orange; font-weight: bold; }
    </style>
    """

    with open(RESERVAS_FILE, "r", encoding="utf-8") as archivo:
        reader = csv.DictReader(archivo)

        for fila in reader:
            html += f"""
            <div class="cita">
              <p><strong>Estado:</strong> <span class="pendiente">{fila['estado']}</span></p>
              <pre>{fila['texto']}</pre>
            </div>
            """

    return html


if __name__ == "__main__":
    app.run(debug=True)
