from flask import Flask, request, jsonify, send_file, redirect
from flask_cors import CORS
from openai import OpenAI
import csv
import os
import uuid

app = Flask(__name__)
CORS(app)

client = OpenAI()
ARCHIVO = "reservas.csv"

historial = [
    {
        "role": "system",
        "content": """Eres el asistente del Restaurante Cortijo Blanco.

Tu trabajo es recoger solicitudes de reserva.

Datos a recoger:
- Nombre
- Número de personas
- Día
- Hora
- Teléfono

Pregunta solo lo que falte.
NO repitas datos que el cliente ya dio.
NO confirmes disponibilidad.

Cuando tengas todo, responde EXACTAMENTE así:

Perfecto, he tomado tu solicitud de reserva.

Nombre: ___
Personas: ___
Día: ___
Hora: ___
Teléfono: ___

El restaurante revisará disponibilidad y te contactará en breve para confirmarla.
"""
    }
]

def guardar_reserva(texto):
    existe = os.path.exists(ARCHIVO)

    with open(ARCHIVO, mode="a", newline="", encoding="utf-8") as file:
        writer = csv.writer(file)

        if not existe:
            writer.writerow(["id", "estado", "reserva"])

        writer.writerow([str(uuid.uuid4()), "pendiente", texto])

@app.route("/")
def home():
    return send_file("index.html")

@app.route("/reservas")
def ver_reservas():
    if not os.path.exists(ARCHIVO):
        return "<h1>Reservas recibidas</h1><p>No hay reservas todavía.</p>"

    html = """
    <h1>Reservas recibidas</h1>
    <a href="/borrar_reservas" style="background:red;color:white;padding:10px;text-decoration:none;">
    Borrar todas las reservas
    </a>
    <br><br>
    """

    with open(ARCHIVO, encoding="utf-8") as file:
        reader = csv.DictReader(file)

        for row in reader:
            estado = row["estado"]
            reserva = row["reserva"]
            reserva_id = row["id"]

            color = "green" if estado == "atendida" else "orange"

            html += f"""
            <div style="border:1px solid #ccc;padding:15px;margin:10px;">
                <strong>Estado:</strong> 
                <span style="color:{color};font-weight:bold;">{estado}</span>
                <pre>{reserva}</pre>
                <a href="/atender/{reserva_id}" style="background:green;color:white;padding:8px;text-decoration:none;">
                Marcar como atendida
                </a>
            </div>
            """

    return html

@app.route("/atender/<reserva_id>")
def atender_reserva(reserva_id):
    if not os.path.exists(ARCHIVO):
        return redirect("/reservas")

    filas = []

    with open(ARCHIVO, encoding="utf-8") as file:
        reader = csv.DictReader(file)
        for row in reader:
            if row["id"] == reserva_id:
                row["estado"] = "atendida"
            filas.append(row)

    with open(ARCHIVO, mode="w", newline="", encoding="utf-8") as file:
        writer = csv.DictWriter(file, fieldnames=["id", "estado", "reserva"])
        writer.writeheader()
        writer.writerows(filas)

    return redirect("/reservas")

@app.route("/borrar_reservas")
def borrar_reservas():
    if os.path.exists(ARCHIVO):
        os.remove(ARCHIVO)
    return redirect("/reservas")

@app.route("/chat", methods=["POST"])
def chat():
    data = request.json
    user_message = data.get("message")

    historial.append({"role": "user", "content": user_message})

    response = client.chat.completions.create(
        model="gpt-4o-mini",
        messages=historial
    )

    reply = response.choices[0].message.content

    if "Perfecto, he tomado tu solicitud de reserva" in reply:
        guardar_reserva(reply)

    historial.append({"role": "assistant", "content": reply})

    return jsonify({"reply": reply})

if __name__ == "__main__":
    app.run(port=5000)
