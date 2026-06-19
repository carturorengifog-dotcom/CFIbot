import os
from telegram import Update, ReplyKeyboardMarkup, KeyboardButton
from telegram.ext import Application, CommandHandler, MessageHandler, filters, ContextTypes
from google import genai
from google.genai import types

# Inicializamos el cliente de Gemini
ai_client = genai.Client()

# Definimos las XIV Áreas de Operación del ACS de CFI de la FAA
AREAS_CFI = [
    ["I. Fundamentals of Instructing", "II. Technical Subject Areas"],
    ["III. Preflight Preparation", "IV. Preflight Lesson on a Maneuver"],
    ["V. Airport Operations", "VI. Takeoffs, Landings, and Go-Arounds"],
    ["VII. Performance Maneuvers", "VIII. Ground Reference Maneuvers"],
    ["IX. Navigation", "X. Slow Flight and Stalls"],
    ["XI. Emergency Operations", "XII. Multiengine Operations"],
    ["XIII. Postflight Procedures", "XIV. Regresar al Menú Principal"]
]

# Instrucción base del sistema para obligar a Gemini a usar los manuales oficiales
INSTRUCCION_BASE = (
    "Actuarás estrictamente como un Examinador de Vuelo (DPE) de la FAA e Instructor de Vuelo Experto. "
    "Tus respuestas deben basarse única y exclusivamente en los manuales oficiales de la FAA: "
    "Pilot's Handbook of Aeronautical Knowledge (FAA-H-8083-25C), Aviation Instructor's Handbook (FAA-H-8083-9B), "
    "Airplane Flying Handbook (FAA-H-8083-3C) y el Airman Certification Standards (FAA-S-ACS-25). "
    "Si el usuario selecciona un área de operación, hazle una pregunta teórica o plantea un escenario "
    "de evaluación basándote en los objetivos de conocimiento, gestión de riesgos o habilidades de esa área del ACS. "
    "Mantén un tono profesional, riguroso y evalúa las respuestas como un verdadero examinador."
)

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Muestra el panel interactivo con las áreas de operación"""
    reply_markup = ReplyKeyboardMarkup(AREAS_CFI, resize_keyboard=True, one_time_keyboard=False)
    
    await update.message.reply_text(
        "✈️ **Bienvenido al Panel de Práctica de CFI** ✈️\n\n"
        "He configurado mi sistema con los manuales oficiales de la FAA.\n"
        "Por favor, selecciona una de las **XIV Áreas de Operación** del ACS en el menú de abajo "
        "para comenzar tu sesión de entrenamiento interactiva con un escenario de examen:",
        reply_markup=reply_markup,
        parse_mode="Markdown"
    )

async def responder(update: Update, context: ContextTypes.DEFAULT_TYPE):
    texto_usuario = update.message.text
    
    # Si el usuario quiere reiniciar el menú
    if "Regresar al Menú" in texto_usuario:
        await start(update, context)
        return

    # Creamos un contexto dinámico según la opción que elija o lo que responda
    prompt_final = texto_usuario
    if any(texto_usuario in fila for fila in AREAS_CFI):
        prompt_final = f"El usuario ha seleccionado repasar la siguiente sección del ACS de CFI: '{texto_usuario}'. Preséntale una pregunta de examen oral o un escenario práctico estricto basado en esa sección."

    try:
        response = ai_client.models.generate_content(
            model='gemini-2.5-flash',
            contents=prompt_final,
            config=types.GenerateContentConfig(
                system_instruction=INSTRUCCION_BASE,
                temperature=0.3
            )
        )
        await update.message.reply_text(response.text)
    except Exception as e:
        await update.message.reply_text("Lo siento, tuve un problema al conectarme con el motor de evaluación.")
        print(f"Error: {e}")

def main():
    TOKEN = os.environ.get("TELEGRAM_TOKEN")
    if not TOKEN:
        print("Error: No se encontró la variable TELEGRAM_TOKEN")
        return

    app = Application.builder().token(TOKEN).build()
    app.add_handler(CommandHandler("start", start))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, responder))
    
    print("Bot de CFI con Panel ACS iniciado correctamente...")
    app.run_polling()

if __name__ == '__main__':
    main()
