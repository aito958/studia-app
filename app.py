import os
from werkzeug.utils import secure_filename
from flask import Flask, render_template, request, jsonify
from agente import chat, cargar_notas, limpiar_historial

app = Flask(__name__)

UPLOAD_FOLDER = os.path.join(os.path.dirname(__file__), "uploads")
os.makedirs(UPLOAD_FOLDER, exist_ok=True)
app.config["UPLOAD_FOLDER"] = UPLOAD_FOLDER
ALLOWED = {"pdf", "txt"}

@app.route("/")
def index():
    return render_template("index.html")

@app.route("/chat", methods=["POST"])
def chat_endpoint():
    datos = request.get_json()
    mensaje = datos.get("mensaje", "").strip()
    if not mensaje:
        return jsonify({"error": "Mensaje vacío"}), 400
    resultado = chat(mensaje)
    return jsonify(resultado)

@app.route("/notas", methods=["GET"])
def notas_endpoint():
    notas = cargar_notas()
    return jsonify({"notas": notas})

@app.route("/limpiar", methods=["POST"])
def limpiar_endpoint():
    limpiar_historial()
    return jsonify({"ok": True, "mensaje": "Historial limpiado"})

@app.route("/estado", methods=["GET"])
def estado_endpoint():
    notas = cargar_notas()
    from agente import historial
    return jsonify({
        "mensajes": len(historial),
        "notas": len(notas),
        "modelo": "openai/gpt-oss-20b"
    })

@app.route("/subir", methods=["POST"])
def subir_archivo():
    if "archivo" not in request.files:
        return jsonify({"error": "No se envió ningún archivo"}), 400
    archivo = request.files["archivo"]
    if not archivo.filename:
        return jsonify({"error": "Archivo vacío"}), 400
    ext = archivo.filename.rsplit(".", 1)[-1].lower()
    if ext not in ALLOWED:
        return jsonify({"error": "Solo PDF y TXT"}), 400
    nombre = secure_filename(archivo.filename)
    ruta = os.path.join(app.config["UPLOAD_FOLDER"], nombre)
    archivo.save(ruta)
    from agente import leer_archivo
    contenido = leer_archivo(ruta)
    resultado = chat(f"El usuario ha subido un archivo llamado '{nombre}'. Este es su contenido:\n\n{contenido}\n\nConfirma que lo has recibido y pregúntale qué quiere hacer con él.")
    return jsonify({"ok": True, "respuesta": resultado.get("respuesta", ""), "nombre": nombre})

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port, debug=False)