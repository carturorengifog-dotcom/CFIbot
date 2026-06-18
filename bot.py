import os
from telegram import Update
from telegram.ext import Application, CommandHandler, MessageHandler, filters, ContextTypes
from google import genai

# Inicializamos el cliente de Gemini (buscará automáticamente la variable GEMINI_API_KEY)
ai_client = genai.Client()

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Respuesta al comando /start"""
    await update.message.reply_text(
        "¡Hola! Soy tu nuevo bot asistido por Gemini. Estoy configurado para actuar como "
        "Examinador de Vuelo (DPE) e Instructor de Vuelo Experto. ¿Qué deseas repasar hoy?"
    )

async def responder(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Recibe el mensaje del usuario y le pide una respuesta a Gemini"""
    texto_usuario = update.message.text
    
    try:
        # Usamos el modelo estándar e inteligente actual (gemini-2.5-flash)
        response = ai_client.models.generate_content(
            model='gemini-2.5-flash',
            contents=texto_usuario,
        )
        await update.message.reply_text(response.text)
    except Exception as e:
        await update.message.reply_text("Lo siento, tuve un problema al procesar tu mensaje.")
        print(f"Error detectado: {e}")

def main():
    # Railway nos dará estos tokens mediante variables de entorno de forma segura
    TOKEN = os.environ.get("TELEGRAM_TOKEN")
    
    if not TOKEN:
        print("Error: No se encontró la variable TELEGRAM_TOKEN")
        return

    app = Application.builder().token(TOKEN).build()
    
    # Configuramos los comandos y mensajes
    app.add_handler(CommandHandler("start", start))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, responder))
    
    print("Bot de Gemini iniciado correctamente en Railway...")
    app.run_polling()

if __name__ == '__main__':
    main()
