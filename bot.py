import os
from telegram import Update
from telegram.ext import Application, CommandHandler, MessageHandler, filters, ContextTypes
from google import genai
from google.genai import types

# Inicializamos el cliente de Gemini
ai_client = genai.Client()

# Definimos la instrucción del sistema para obligarlo a actuar bajo las normas FAA
INSTRUCCION_FAA = (
    "Actuarás única y exclusivamente como un Examinador de Vuelo (DPE) e Instructor de Vuelo Experto de la FAA. "
    "Tus respuestas deben basarse estrictamente en los manuales oficiales de la FAA (como el Pilot's Handbook of Aeronautical Knowledge, "
    "Airplane Flying Handbook, y los Airman Certification Standards). Si el usuario te pregunta algo que no esté regulado, "
    "contemplado o fundamentado en los manuales oficiales de la FAA, debes responder textualmente: "
    "'Lo siento, como instructor enfocado en estándares FAA, solo puedo responder preguntas basadas estrictamente en sus manuales oficiales.' "
    "No inventes información, no uses fuentes externas y mantén un tono profesional, preciso y de examinador."
)

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "¡Hola! Soy tu instructor de vuelo experto. Estoy configurado para responder "
        "únicamente basándome en los manuales oficiales de la FAA. ¿Qué área o regulación deseas repasar hoy?"
    )

async def responder(update: Update, context: ContextTypes.DEFAULT_TYPE):
    texto_usuario = update.message.text
    
    try:
        # Usamos la instrucción del sistema para moldear el comportamiento del modelo
        response = ai_client.models.generate_content(
            model='gemini-2.5-flash',
            contents=texto_usuario,
            config=types.GenerateContentConfig(
                system_instruction=INSTRUCCION_FAA,
                temperature=0.1 # Temperatura baja para evitar "alucinaciones" y mantenerlo estricto
            )
        )
        await update.message.reply_text(response.text)
    except Exception as e:
        await update.message.reply_text("Lo siento, tuve un problema al procesar tu mensaje.")
        print(f"Error detectado: {e}")

def main():
    TOKEN = os.environ.get("TELEGRAM_TOKEN")
    if not TOKEN:
        print("Error: No se encontró la variable TELEGRAM_TOKEN")
        return

    app = Application.builder().token(TOKEN).build()
    app.add_handler(CommandHandler("start", start))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, responder))
    
    print("Bot de Gemini iniciado correctamente en Railway...")
    app.run_polling()

if __name__ == '__main__':
    main()
