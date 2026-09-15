import os
import re
import json
from datetime import datetime
from pathlib import Path
from groq import Groq
from dotenv import load_dotenv
import wikipediaapi

# ----------------------------------------------------------
# CONFIGURACIÓN INICIAL
# ----------------------------------------------------------
load_dotenv(Path(__file__).parent / ".env")

api_key = os.getenv("GROQ_API_KEY")
if not api_key:
    raise RuntimeError("No se encontró GROQ_API_KEY en el .env")

cliente = Groq(api_key=api_key)
wiki = wikipediaapi.Wikipedia(language="es", user_agent="studia-agente/1.0")

MODELO = "openai/gpt-oss-20b"
MAX_MENSAJES = 20
MEMORIA_PATH = Path(__file__).parent / "memoria.json"
NOTAS_PATH = Path(__file__).parent / "notas.json"

# ----------------------------------------------------------
# SYSTEM PROMPT — Tutor de informática especializado
# ----------------------------------------------------------
SYSTEM_PROMPT = {
    "role": "system",
    "content": (
        "Eres **StudIA**, un asistente de IA especializado en ayudar a estudiantes de "
        "informática. Tu especialidad es:\n"
        "1. **Corregir ejercicios** - Revisa código, encuentra errores, sugiere mejoras.\n"
        "2. **Asistente de apuntes** - Genera y organiza apuntes sobre programación, "
        "algoritmos, bases de datos, redes, sistemas operativos, etc.\n"
        "3. **Explicar conceptos** y **generar ejercicios de práctica**.\n\n"
        "REGLAS DE USO DE HERRAMIENTAS (¡muy importante!):\n"
        "- Si el usuario pide GUARDAR o CREAR una NOTA → usa guardar_nota(tema, contenido).\n"
        "- Si el usuario pide BUSCAR, VER o RECORDAR una NOTA → usa buscar_nota(tema).\n"
        "- Si el usuario pide EXPLICAR CÓDIGO → usa explicar_codigo(codigo, lenguaje).\n"
        "- Si el usuario pide CORREGIR un EJERCICIO → usa corregir_ejercicio(enunciado, codigo, lenguaje).\n"
        "- Si el usuario pide GENERAR un EJERCICIO → usa generar_ejercicio(tema, dificultad).\n"
        "- Si el usuario pide RESUMIR TEXTO → usa resumir_texto(texto).\n"
        "- Si el usuario pide la HORA → usa get_hora_actual().\n"
        "- Si el usuario pide HACER CUENTAS → usa calcular(expresion).\n"
        "- Si el usuario pide BUSCAR información → usa buscar_wikipedia(termino).\n\n"
        "REGLA CLAVE: Cuando una herramienta (nota, cálculo, wikipedia, etc.)\n"
        "devuelve un resultado, DEBES incluir esa información textualmente en tu "
        "respuesta. Por ejemplo, si buscar_nota devuelve el contenido de una nota, "
        "muéstralo al usuario. Si calcular devuelve un resultado, inclú-yelo. "
        "Si Wikipedia devuelve un texto, cita los puntos clave.\n\n"
        "Siempre responde en español, tono amable y didáctico. Usa markdown."
    )
}

# ----------------------------------------------------------
# MEMORIA: cargar y guardar historial de conversación
# ----------------------------------------------------------
def cargar_historial():
    """Carga el historial guardado en memoria.json."""
    if MEMORIA_PATH.exists():
        try:
            return json.loads(MEMORIA_PATH.read_text(encoding="utf-8"))
        except Exception:
            return []
    return []

def guardar_historial(historial):
    """Guarda el historial en memoria.json (sin el system prompt)."""
    sin_system = [m for m in historial if isinstance(m, dict) and m.get("role") != "system"]
    MEMORIA_PATH.write_text(
        json.dumps(sin_system, ensure_ascii=False, indent=2),
        encoding="utf-8"
    )


def limpiar_historial():
    """Borra el historial de conversación y lo reinicia con solo el system prompt."""
    global historial
    historial[:] = [SYSTEM_PROMPT]
    if MEMORIA_PATH.exists():
        MEMORIA_PATH.write_text("[]", encoding="utf-8")

# ----------------------------------------------------------
# NOTAS: sistema de guardado y búsqueda de apuntes
# ----------------------------------------------------------
def cargar_notas():
    """Carga las notas guardadas en notas.json."""
    if NOTAS_PATH.exists():
        try:
            return json.loads(NOTAS_PATH.read_text(encoding="utf-8"))
        except Exception:
            return {}
    return {}

def guardar_nota(tema, contenido):
    """Guarda una nota bajo el tema especificado."""
    notas = cargar_notas()
    notas[tema.lower()] = {
        "tema": tema,
        "contenido": contenido,
        "fecha": datetime.now().strftime("%Y-%m-%d %H:%M")
    }
    NOTAS_PATH.write_text(
        json.dumps(notas, ensure_ascii=False, indent=2),
        encoding="utf-8"
    )
    return f"Nota guardada sobre: {tema}"

def buscar_nota(tema):
    """Busca una nota por tema o palabra clave."""
    notas = cargar_notas()
    tema_lower = tema.lower()
    for clave, valor in notas.items():
        if tema_lower in clave or tema_lower in valor.get("tema", "").lower():
            n = valor
            return (
                f"**Tema:** {n['tema']}\n"
                f"**Fecha:** {n['fecha']}\n\n"
                f"{n['contenido']}"
            )
    return f"No encontré ninguna nota sobre '{tema}'. Usa guardar_nota para crear una."

# ----------------------------------------------------------
# HERRAMIENTAS BÁSICAS
# ----------------------------------------------------------
def get_hora_actual():
    ahora = datetime.now()
    return f"Son las {ahora.strftime('%H:%M')} del {ahora.strftime('%d/%m/%Y')}"

def calcular(expresion: str):
    try:
        if re.fullmatch(r"[\d\s\+\-\*\/\.\(\)]+", expresion):
            resultado = eval(expresion)
            return f"{expresion} = {resultado}"
        else:
            return "Expresión no válida. Usa solo números y operadores + - * /"
    except Exception as e:
        return f"Error al calcular: {e}"

def buscar_wikipedia(termino: str):
    try:
        pagina = wiki.page(termino)
        if pagina.exists():
            return pagina.summary[:500] + "..."
        return f"No encontré información sobre '{termino}' en Wikipedia."
    except Exception as e:
        return f"Error al buscar en Wikipedia: {e}"

# ----------------------------------------------------------
# HERRAMIENTAS CON IA (usan la API de Groq internamente)
# ----------------------------------------------------------
def _llamada_simple(prompt_sistema: str, mensaje_usuario: str) -> str:
    """Helper: llama a la API con un system prompt específico y un solo mensaje."""
    try:
        r = cliente.chat.completions.create(
            model=MODELO,
            messages=[
                {"role": "system", "content": prompt_sistema},
                {"role": "user", "content": mensaje_usuario}
            ]
        )
        return (r.choices[0].message.content or "").strip()
    except Exception as e:
        return f"Error al consultar la IA: {e}"

def explicar_codigo(codigo: str, lenguaje: str = "python"):
    """Explica paso a paso qué hace un fragmento de código."""
    prompt = (
        f"Eres un profesor de programación. Explica a un estudiante qué hace "
        f"el siguiente código en {lenguaje}, línea por línea. Sé claro y usa "
        f"ejemplos simples. Usa formato markdown."
    )
    return _llamada_simple(prompt, f"Lenguaje: {lenguaje}\n\n```\n{codigo}\n```")

def corregir_ejercicio(enunciado: str, codigo: str, lenguaje: str = "python"):
    """Revisa y corrige código de un ejercicio."""
    prompt = (
        f"Eres un profesor corrigiendo un ejercicio. Analiza el código, identifica "
        f"errores, sugiere mejoras y explica cada hallazgo. Usa formato markdown."
    )
    mensaje = f"ENUNCIADO:\n{enunciado}\n\nCÓDIGO ({lenguaje}):\n```\n{codigo}\n```"
    return _llamada_simple(prompt, mensaje)

def generar_ejercicio(tema: str, dificultad: str = "intermedio"):
    """Genera un ejercicio de programación completo."""
    prompt = (
        f"Eres un docente que genera ejercicios de programación. Crea un ejercicio "
        f"completo sobre '{tema}' con dificultad '{dificultad}'. Incluye enunciado, "
        f"ejemplos de entrada/salida, pistas y solución. Usa markdown."
    )
    return _llamada_simple(prompt, f"Tema: {tema}\nDificultad: {dificultad}")

def resumir_texto(texto: str):
    """Resume un texto largo en puntos clave."""
    prompt = (
        "Eres un asistente que resume textos académicos. Lee el texto y produce un "
        "resumen conciso con viñetas de los puntos clave. Mantén términos técnicos. "
        "Usa formato markdown."
    )
    return _llamada_simple(prompt, texto)


# ----------------------------------------------------------
# DESCRIPCIÓN DE LAS HERRAMIENTAS PARA LA IA
# ----------------------------------------------------------
herramientas = [
    {
        "type": "function",
        "function": {
            "name": "get_hora_actual",
            "description": "Devuelve la hora y fecha actual del sistema",
            "parameters": {"type": "object", "properties": {}, "required": []}
        }
    },
    {
        "type": "function",
        "function": {
            "name": "calcular",
            "description": "Calcula una expresión matemática. Úsala cuando el usuario pida hacer cuentas.",
            "parameters": {
                "type": "object",
                "properties": {
                    "expresion": {
                        "type": "string",
                        "description": "La expresión matemática a calcular, por ejemplo: 25 * 4 + 10"
                    }
                },
                "required": ["expresion"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "buscar_wikipedia",
            "description": "Busca información sobre un tema en Wikipedia en español.",
            "parameters": {
                "type": "object",
                "properties": {
                    "termino": {
                        "type": "string",
                        "description": "El término o tema a buscar, por ejemplo: Python, Madrid, fotosíntesis"
                    }
                },
                "required": ["termino"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "explicar_codigo",
            "description": "Explica paso a paso qué hace un fragmento de código. Úsala cuando el usuario pida entender algo de código.",
            "parameters": {
                "type": "object",
                "properties": {
                    "codigo": {
                        "type": "string",
                        "description": "El código a explicar"
                    },
                    "lenguaje": {
                        "type": "string",
                        "description": "El lenguaje de programación (python, java, javascript, c, cpp, etc.)",
                        "default": "python"
                    }
                },
                "required": ["codigo"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "corregir_ejercicio",
            "description": "Revisa y corrige código de un ejercicio: encuentra errores, sugiere mejoras y explica por qué.",
            "parameters": {
                "type": "object",
                "properties": {
                    "enunciado": {
                        "type": "string",
                        "description": "El enunciado del ejercicio"
                    },
                    "codigo": {
                        "type": "string",
                        "description": "El código escrito por el estudiante"
                    },
                    "lenguaje": {
                        "type": "string",
                        "description": "El lenguaje de programación (python, java, javascript, etc.)",
                        "default": "python"
                    }
                },
                "required": ["enunciado", "codigo"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "generar_ejercicio",
            "description": "Genera un ejercicio de programación completo sobre un tema y dificultad específicos.",
            "parameters": {
                "type": "object",
                "properties": {
                    "tema": {
                        "type": "string",
                        "description": "El tema del ejercicio, por ejemplo: recursividad, pilas, SQL, POO"
                    },
                    "dificultad": {
                        "type": "string",
                        "description": "Nivel de dificultad: facil, intermedio o avanzado",
                        "default": "intermedio"
                    }
                },
                "required": ["tema"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "resumir_texto",
            "description": "Resume un texto largo en puntos clave. Ideal para resumir apuntes teóricos.",
            "parameters": {
                "type": "object",
                "properties": {
                    "texto": {
                        "type": "string",
                        "description": "El texto a resumir"
                    }
                },
                "required": ["texto"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "guardar_nota",
            "description": "Guarda una nota de estudio sobre un tema específico para recordarla después.",
            "parameters": {
                "type": "object",
                "properties": {
                    "tema": {
                        "type": "string",
                        "description": "El tema o titulo de la nota, por ejemplo: Recursividad, Estructuras de datos"
                    },
                    "contenido": {
                        "type": "string",
                        "description": "El contenido de la nota con lo que quieres recordar"
                    }
                },
                "required": ["tema", "contenido"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "buscar_nota",
            "description": "Busca una nota de estudio guardada previamente por tema o palabra clave.",
            "parameters": {
                "type": "object",
                "properties": {
                    "tema": {
                        "type": "string",
                        "description": "El tema o palabra clave a buscar en las notas guardadas"
                    }
                },
                "required": ["tema"]
            }
        }
    }
]

# ----------------------------------------------------------
# FUNCIÓN QUE EJECUTA LA HERRAMIENTA QUE PIDA LA IA
# ----------------------------------------------------------
def ejecutar_herramienta(nombre, argumentos):
    if nombre == "get_hora_actual":
        return get_hora_actual()
    elif nombre == "calcular":
        return calcular(argumentos.get("expresion", ""))
    elif nombre == "buscar_wikipedia":
        return buscar_wikipedia(argumentos.get("termino", ""))
    elif nombre == "explicar_codigo":
        return explicar_codigo(
            argumentos.get("codigo", ""),
            argumentos.get("lenguaje", "python")
        )
    elif nombre == "corregir_ejercicio":
        return corregir_ejercicio(
            argumentos.get("enunciado", ""),
            argumentos.get("codigo", ""),
            argumentos.get("lenguaje", "python")
        )
    elif nombre == "generar_ejercicio":
        return generar_ejercicio(
            argumentos.get("tema", ""),
            argumentos.get("dificultad", "intermedio")
        )
    elif nombre == "resumir_texto":
        return resumir_texto(argumentos.get("texto", ""))
    elif nombre == "guardar_nota":
        return guardar_nota(
            argumentos.get("tema", ""),
            argumentos.get("contenido", "")
        )
    elif nombre == "buscar_nota":
        return buscar_nota(argumentos.get("tema", ""))
    else:
        return f"Herramienta '{nombre}' no reconocida."


# ----------------------------------------------------------
# HISTORIAL: cargamos al arrancar
# ----------------------------------------------------------
historial = [SYSTEM_PROMPT] + cargar_historial()


# ----------------------------------------------------------
# ROUTING POR PALABRAS CLAVE (respaldo para notas)
# ----------------------------------------------------------
def _intent_routing(mensaje_usuario: str):
    """
    Si el mensaje claramente pide guardar o buscar una nota,
    ejecuta la herramienta directamente (respaldo cuando el
    modelo no la elige).
    Devuelve (herramienta, resultado) o (None, None) si no aplica.
    """
    import re as _re
    msg_lower = mensaje_usuario.lower()

    # --- Guardar nota ---
    if "guarda" in msg_lower and "nota" in msg_lower:
        # Extraer tema: después de "sobre"
        tema_match = _re.search(r'sobre\s+(.+?)(?:\s+(?:con|con contenido|el contenido)|\.|$)', mensaje_usuario, _re.IGNORECASE)
        tema = tema_match.group(1).strip().rstrip('.') if tema_match else "Sin tema"

        # Extraer contenido: después de "con:" o "con contenido:"
        contenido_match = _re.search(r'(?:con[:：]\s*|\bcontenido[:：]\s*)([\s\S]+)', mensaje_usuario, _re.IGNORECASE)
        contenido = contenido_match.group(1).strip() if contenido_match else ""

        if contenido and tema:
            return "guardar_nota", guardar_nota(tema, contenido)

    # --- Buscar nota ---
    if "busca" in msg_lower and "nota" in msg_lower:
        # Extraer tema: después de "nota sobre" o después de "sobre"
        tema_match = _re.search(r'sobre\s+(.+?)(?:\s|$|,|\.)', mensaje_usuario, _re.IGNORECASE)
        tema = tema_match.group(1).strip().rstrip('.') if tema_match else ""

        if tema:
            return "buscar_nota", buscar_nota(tema)

    return None, None


# ----------------------------------------------------------
# FUNCIÓN PRINCIPAL (usada por app.py)
# ----------------------------------------------------------
def chat(mensaje_usuario: str):
    """Procesa un mensaje del usuario y devuelve la respuesta de la IA."""
    historial.append({"role": "user", "content": mensaje_usuario})

    herramienta_usada = None

    try:
        respuesta = cliente.chat.completions.create(
            model=MODELO,
            messages=historial,
            tools=herramientas,
            tool_choice="auto"
        )
    except Exception as e:
        historial.pop()
        return {"error": str(e), "herramienta": None}

    mensaje = respuesta.choices[0].message

    if mensaje.tool_calls:
        # Convertir a dict con solo los campos soportados + tool_calls serializables
        msg_dict = {
            "role": mensaje.role,
            "content": mensaje.content,
        }
        if mensaje.tool_calls:
            msg_dict["tool_calls"] = [
                {
                    "id": tc.id,
                    "type": tc.type,
                    "function": {
                        "name": tc.function.name,
                        "arguments": tc.function.arguments
                    }
                }
                for tc in mensaje.tool_calls
            ]
        historial.append(msg_dict)

        for tool_call in mensaje.tool_calls:
            nombre = tool_call.function.name
            argumentos = json.loads(tool_call.function.arguments or "{}")
            resultado = ejecutar_herramienta(nombre, argumentos)
            herramienta_usada = nombre
            historial.append({
                "role": "tool",
                "tool_call_id": tool_call.id,
                "content": resultado
            })

        try:
            respuesta_final = cliente.chat.completions.create(
                model=MODELO,
                messages=historial,
                tools=herramientas
            )
            mensaje_ia = respuesta_final.choices[0].message.content or ""
        except Exception as e:
            return {"error": str(e), "herramienta": herramienta_usada}

    else:
        # Fallback: routing por palabras clave si el modelo no usó herramientas
        tool_name, tool_result = _intent_routing(mensaje_usuario)
        if tool_name:
            herramienta_usada = tool_name
            historial.append({
                "role": "tool",
                "tool_call_id": f"fallback_{tool_name}",
                "content": tool_result
            })
            try:
                respuesta_final = cliente.chat.completions.create(
                    model=MODELO,
                    messages=historial
                )
                mensaje_ia = respuesta_final.choices[0].message.content or tool_result
            except Exception:
                mensaje_ia = tool_result
        else:
            mensaje_ia = mensaje.content or ""

    mensaje_ia = mensaje_ia.strip()

    # Limitar tamaño del historial
    if len(historial) > MAX_MENSAJES:
        historial[:] = [historial[0]] + historial[-(MAX_MENSAJES - 1):]

    # Guardar en memoria persistente
    guardar_historial(historial)

    return {"respuesta": mensaje_ia, "herramienta": herramienta_usada}


# ----------------------------------------------------------
# MODO CLI (opcional): python agente.py
# ----------------------------------------------------------
if __name__ == "__main__":
    print("StudIA — Tu asistente de estudio de informática")
    print("Escribe 'salir' para terminar.\n")

    while True:
        mensaje_usuario = input("Tú: ")
        if mensaje_usuario.lower() == "salir":
            print("¡Hasta luego! 📚")
            break

        resultado = chat(mensaje_usuario)
        if resultado.get("error"):
            print(f"Error: {resultado['error']}")
        else:
            if resultado["herramienta"]:
                print(f"[Herramienta: {resultado['herramienta']}]")
            print(f"IA: {resultado['respuesta']}\n")
