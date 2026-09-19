📚 StudIA — Tu Tutor de Informática con IA

Agente de inteligencia artificial especializado en ayudar a estudiantes de informática. Corrige código, genera ejercicios, explica conceptos y organiza tus apuntes. Todo desde el navegador.

✨ ¿Qué puede hacer?
Herramienta	Descripción
- Corregir ejercicios	Pega tu código y te dice qué falla, por qué y cómo mejorarlo 
- Explicar código	Explica línea a línea qué hace cualquier fragmento
- Generar ejercicios	Crea ejercicios con enunciado, ejemplos y solución
- Resumir apuntes	Pega texto largo y obtén los puntos clave
-Sistema de notas	Guarda y recupera apuntes entre sesiones
-Subir archivos	        Lee PDFs y TXTs de tus apuntes directamente
-Calculadora	        Resuelve expresiones matemáticas
- Wikipedia	        Busca información en tiempo real
- Hora actual	        Consulta la hora y fecha del sistema


  Tecnologías
  
Python + Flask — servidor web
Groq API — modelo de lenguaje (openai/gpt-oss-20b)
HTML/CSS/JS — interfaz web con diseño oscuro
Railway — despliegue en producción
Wikipedia API — búsqueda de información
PyPDF2 — lectura de archivos PDF


**🚀 Instalación **local**

1. Clona el repositorio
bash
git clone https://github.com/aito958/studia-app.git
cd studia-app
2. Instala las dependencias
bash
pip install -r requirements.txt
3. Crea el archivo .env
GROQ_API_KEY=tu_api_key_aqui

Consigue tu API key gratis en console.groq.com

4. Arranca el servidor
bash
python app.py
5. Abre el navegador
http://localhost:5000
📁 Estructura del proyecto
studia-app/
├── app.py              # Servidor Flask y rutas de la API

├── agente.py           # Lógica del agente de IA y herramientas

├── requirements.txt    # Dependencias Python

├── Procfile            # Configuración para Railway

├── runtime.txt         # Versión de Python

├── templates/
│   └── index.html      # Interfaz web

└── uploads/            # Archivos subidos por el usuario

🌐 Rutas de la API
Método	Ruta	Descripción

GET	/	Interfaz web

POST	/chat	Enviar mensaje al agente

POST	/subir	Subir archivo PDF o TXT

GET	/notas	Ver todas las notas guardadas

POST	/limpiar	Borrar historial de conversación

GET	/estado	Estado del agente (mensajes, notas, modelo)


**💡 Ejemplos de uso

Corregir código Java:

Corrige este código en Java:
public class Main {
    public static void main(String[] args) {
        int[] numeros = {1, 2, 3};
        System.out.println(numeros[5]);
    }
}

Generar un ejercicio:

Genera un ejercicio sobre recursividad nivel intermedio

Guardar una nota: 

Guarda una nota sobre POO con: La herencia permite...

Resumir apuntes:

Resume este texto: [pega tus apuntes aquí]

**👤 Autor

Aitor — Estudiante de Desarrollo de Aplicaciones Web (DAW)

Proyecto construido desde cero aprendiendo Python, Flask y la API de Groq.

📄 Licencia

MIT — úsalo, modifícalo y mejóralo libremente.
