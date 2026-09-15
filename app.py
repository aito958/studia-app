import os

from flask import Flask, render_template, request, jsonify
from agente import chat, cargar_notas, limpiar_historial

app = Flask(__name__)


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
    """Devuelve todas las notas guardadas."""
    notas = cargar_notas()
    return jsonify({"notas": notas})


@app.route("/limpiar", methods=["POST"])
def limpiar_endpoint():
    """Borra el historial de conversación y las notas (opcional)."""
    limpiar_historial()
    return jsonify({"ok": True, "mensaje": "Historial limpiado"})


@app.route("/estado", methods=["GET"])
def estado_endpoint():
    """Devuelve información sobre el estado actual."""
    notas = cargar_notas()
    from agente import historial
    return jsonify({
        "mensajes": len(historial),
        "notas": len(notas),
        "modelo": "openai/gpt-oss-20b"
    })


if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port, debug=False)