from flask import Flask, request, jsonify, send_file
from flask_cors import CORS
from openai import OpenAI
import csv
import os
from datetime import datetime

app = Flask(__name__)
CORS(app)

client = OpenAI()

RESERVAS_FILE="citas.csv"


def crear_historial():

    return [

        {

            "role":"system",

            "content":"""

Eres un asistente profesional para gestionar citas en consultas, clínicas, dentistas y psicólogos.

Tu trabajo es recoger:

- Nombre
- Motivo de la cita
- Día
- Hora
- Teléfono

NO hables de restaurantes.
NO preguntes cuántas personas son.

Cuando tengas todos los datos responde EXACTAMENTE:

Perfecto, he tomado tu solicitud de cita.

Nombre: ...
Motivo: ...
Día: ...
Hora: ...
Teléfono: ...

El negocio revisará disponibilidad y te contactará en breve para confirmarla.

"""

        }

    ]


def guardar_cita(texto):

    if "Perfecto, he tomado tu solicitud de cita." not in texto:
        return

    existe=os.path.exists(
        RESERVAS_FILE
    )

    with open(
        RESERVAS_FILE,
        "a",
        newline="",
        encoding="utf-8"
    ) as archivo:

        writer=csv.writer(
            archivo
        )

        if not existe:

            writer.writerow([

                "fecha_registro",
                "estado",
                "texto"

            ])

        writer.writerow([

            datetime.now().strftime(
                "%Y-%m-%d %H:%M:%S"
            ),

            "pendiente",

            texto

        ])



@app.route("/")
def home():

    return send_file(
        "index.html"
    )


@app.route(
    "/chat",
    methods=["POST"]
)

def chat():

    data=request.get_json()

    mensaje=data.get(
        "message",
        ""
    )

    historial=crear_historial()

    historial.append({

        "role":"user",
        "content":mensaje

    })

    respuesta=client.chat.completions.create(

        model="gpt-4o-mini",

        messages=historial

    )

    reply=respuesta.choices[0].message.content

    guardar_cita(
        reply
    )

    return jsonify({

        "reply":reply

    })


@app.route("/reservas")
def ver_reservas():

    if not os.path.exists(
        RESERVAS_FILE
    ):

        return """

        <h1>Citas recibidas</h1>
        <p>No hay citas todavía.</p>

        """

    html="""

    <h1>Citas recibidas</h1>

    <style>

    body{

    font-family:Arial;
    padding:30px;

    }

    .cita{

    border:1px solid #ccc;
    padding:20px;
    border-radius:10px;
    margin-bottom:20px;

    }

    .pendiente{

    color:orange;
    font-weight:bold;

    }

    button{

    padding:10px;
    border:none;
    border-radius:8px;
    margin-right:10px;
    cursor:pointer;

    }

    </style>

    """


    with open(
        RESERVAS_FILE,
        "r",
        encoding="utf-8"
    ) as archivo:

        reader=csv.DictReader(
            archivo
        )

        for fila in reader:

            telefono=""

            for linea in fila[
                "texto"
            ].split("\n"):

                if "Teléfono:" in linea:

                    telefono=linea.replace(
                        "Teléfono:",
                        ""
                    ).strip()

            aceptar=f"https://wa.me/34{telefono}?text=Hola,%20tu%20cita%20ha%20sido%20confirmada%20✅"

            rechazar=f"https://wa.me/34{telefono}?text=Hola,%20lo%20sentimos,%20ahora%20mismo%20no%20tenemos%20disponibilidad."


            html += f"""

            <div class="cita">

            <p>

            <strong>Estado:</strong>

            <span class="pendiente">

            {fila['estado']}

            </span>

            </p>

            <pre>

{fila['texto']}

            </pre>

            <br><br>

            <a href="{aceptar}" target="_blank">

            <button>

            ✅ Aceptar WhatsApp

            </button>

            </a>

            <a href="{rechazar}" target="_blank">

            <button>

            ❌ Rechazar WhatsApp

            </button>

            </a>

            </div>

            """

    return html


if __name__=="__main__":

    app.run(
        debug=True
    )
