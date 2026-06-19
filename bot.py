import os
import random
from telegram import Update, ReplyKeyboardMarkup
from telegram.ext import Application, CommandHandler, MessageHandler, filters, ContextTypes
from google import genai
from google.genai import types

# Inicializamos el cliente de Gemini
ai_client = genai.Client()

# Diccionario oficial con las XIV Áreas de Operación del ACS de CFI y sus Tareas
ESTRUCTURA_ACS = {
    "I. Fundamentals of Instructing": [
        "Task A: Human Behavior",
        "Task B: The Learning Process",
        "Task C: Effective Communication",
        "Task D: The Teaching Process",
        "Task E: Assessment",
        "Task F: Flight Instructor Characteristics",
        "Task G: Elements of Effective Instruction"
    ],
    "II. Technical Subject Areas": [
        "Task A: Aeromedical Factors",
        "Task B: Visual Inspection & Airworthiness",
        "Task C: Principles of Flight",
        "Task D: Airplane Flight Controls",
        "Task E: Airplane Systems",
        "Task F: Navigation & Flight Planning",
        "Task G: Night Operations",
        "Task H: High-Altitude Operations",
        "Task I: Regulations & Endorsements"
    ],
    "III. Preflight Preparation": [
        "Task A: Pilot Certificates & Documents",
        "Task B: Weather Information",
        "Task C: Operation of Systems",
        "Task D: Performance & Limitations",
        "Task E: Airworthiness Requirements"
    ],
    "IV. Preflight Lesson on a Maneuver": [
        "Task A: Maneuver Lesson Description"
    ],
    "V. Airport Operations": [
        "Task A: Radio Communications",
        "Task B: Airport Markings & Lighting",
        "Task C: Shotfield/Softfield Operations"
    ],
    "VI. Takeoffs, Landings, and Go-Arounds": [
        "Task A: Normal Takeoff & Climb",
        "Task B: Crosswind Takeoff & Climb",
        "Task C: Short-Field Takeoff & Climb",
        "Task D: Soft-Field Takeoff & Climb",
        "Task E: Normal Approach & Landing",
        "Task F: Slip to a Landing",
        "Task G: Go-Around / Rejected Landing"
    ],
    "VII. Performance Maneuvers": [
        "Task A: Steep Turns",
        "Task B: Steep Spirals",
        "Task C: Chandelles",
        "Task D: Lazy Eights"
    ],
    "VIII. Ground Reference Maneuvers": [
        "Task A: Rectangular Course",
        "Task B: S-Turns",
        "Task C: Turns Around a Point"
    ],
    "IX. Navigation": [
        "Task A: Pilotage & Dead Reckoning",
        "Task B: Navigation Systems",
        "Task C: Diversion / Lost Procedures"
    ],
    "X. Slow Flight and Stalls": [
        "Task A: Maneuvering in Slow Flight",
        "Task B: Power-On Stalls",
        "Task C: Power-Off Stalls",
        "Task D: Accelerated Stalls",
        "Task E: Spin Awareness"
    ],
    "XI. Emergency Operations": [
        "Task A: Emergency Approach & Landing",
        "Task B: Systems & Equipment Malfunctions",
        "Task C: Emergency Descent"
    ],
    "XII. Multiengine Operations": [
        "Task A: Engine Failure After Takeoff",
        "Task B: VMC Demonstration",
        "Task C: One-Engine Inoperative Approach"
    ],
    "XIII. Postflight Procedures": [
        "Task A: Postflight Procedures"
    ],
    "XIV. Plan of Action": [
        "Task A: Developing a Plan of Action"
    ]
}

# El menú principal ahora respeta de forma estricta las XIV áreas en pares limpios
MENU_PRINCIPAL = [
    ["I. Fundamentals of Instructing", "II. Technical Subject Areas"],
    ["III. Preflight Preparation", "IV. Preflight Lesson on a Maneuver"],
    ["V. Airport Operations", "VI. Takeoffs, Landings, and Go-Arounds"],
    ["VII. Performance Maneuvers", "VIII. Ground Reference Maneuvers"],
    ["IX. Navigation", "X. Slow Flight and Stalls"],
    ["XI. Emergency Operations", "XII. Multiengine Operations"],
    ["XIII. Postflight Procedures", "XIV. Plan of Action"],
    ["🔄 Reset / Volver al Inicio"]
]

INSTRUCCION_DPE = (
    "Actuarás rigurosamente como un Examinador de Vuelo (DPE) de la FAA e Instructor de Vuelo Experto. "
    "Tu objetivo es evaluar y preparar a un candidato a certificado de CFI de avión.\n\n"
    "Usa exclusivamente como base teórica y normativa los siguientes manuales oficiales:\n"
    "- Pilot's Handbook of Aeronautical Knowledge (FAA-H-8083-25C)\n"
    "- Aviation Instructor's Handbook (FAA-H-8083-9B)\n"
    "- Airplane Flying Handbook (FAA-H-8083-3C)\n"
    "- Flight Instructor for Airplane Category Airman Certification Standards (FAA-S-ACS-25)\n\n"
    "Cuando se te indique un Área de Operación y una Tarea (Task) del ACS, debes formular INMEDIATAMENTE una "
    "pregunta de examen clara, directa y técnica que un examinador real haría en el examen práctico oral. "
    "Puedes enfocar la pregunta en un elemento de Conocimiento (K), Gestión de Riesgos (R) o Habilidad (S) de dicha Task. "
    "Si el usuario responde a tu pregunta, evalúa su respuesta críticamente, corrígelo con referencias exactas "
    "del manual de la FAA si se equivoca, y mantén la simulación viva."
)

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data["area_actual"] = None
    reply_markup = ReplyKeyboardMarkup(MENU_PRINCIPAL, resize_keyboard=True)
    
    await update.message.reply_text(
        "✈️ **Sistema de Evaluación DPE - Certificado CFI (ACS Oficial)** ✈️\n\n"
        "Selecciona el **Área de Operación** (I al XIV) que deseas evaluar para desplegar sus Tasks y lanzar una pregunta de examen:",
        reply_markup=reply_markup,
        parse_mode="Markdown"
    )

async def manejar_mensaje(update: Update, context: ContextTypes.DEFAULT_TYPE):
    texto = update.message.text
    
    if texto == "🔄 Reset / Volver al Inicio":
        await start(update, context)
        return

    # Si elige un Área de Operación válida
    if texto in ESTRUCTURA_ACS:
        context.user_data["area_actual"] = texto
        
        tareas = ESTRUCTURA_ACS[texto]
        botones_tareas = [[tarea] for tarea in tareas]
        botones_tareas.append(["💡 Pregunta Aleatoria de esta Área"])
        botones_tareas.append(["⬅️ Volver al Menú de Áreas"])
        
        reply_markup = ReplyKeyboardMarkup(botones_tareas, resize_keyboard=True)
        await update.message.reply_text(
            f"📂 **{texto}**\n\nSelecciona una **Task** específica para iniciar la pregunta del examen oral:",
            reply_markup=reply_markup,
            parse_mode="Markdown"
        )
        return

    if texto == "⬅️ Volver al Menú de Áreas":
        await start(update, context)
        return

    # Si selecciona una Task o la pregunta aleatoria dentro de un área activa
    area_activa = context.user_data.get("area_actual")
    if area_activa and (texto in ESTRUCTURA_ACS[area_activa] or "Pregunta Aleatoria" in texto):
        prompt_solicitud = (
            f"El candidato está listo para ser evaluado en '{area_activa}', específicamente bajo la opción '{texto}'. "
            f"Genera inmediatamente una pregunta interactiva y profunda basada en el estándar ACS de la FAA para esta sección."
        )
        await enviar_a_gemini(update, prompt_solicitud)
        return

    # Si es una respuesta a una pregunta abierta del bot
    if area_activa:
        prompt_respuesta = (
            f"El usuario está respondiendo a tu pregunta anterior sobre el '{area_activa}'. "
            f"Su respuesta fue: '{texto}'. Evalúala críticamente de acuerdo con los manuales de la FAA y retroalimenta."
        )
        await enviar_a_gemini(update, prompt_respuesta)
    else:
        await update.message.reply_text("Por favor, selecciona primero un Área de Operación en el menú para comenzar.")

async def enviar_a_gemini(update: Update, prompt: str):
    try:
        response = ai_client.models.generate_content(
            model='gemini-2.5-flash',
            contents=prompt,
            config=types.GenerateContentConfig(
                system_instruction=INSTRUCCION_DPE,
                temperature=0.4
            )
        )
        await update.message.reply_text(response.text)
    except Exception as e:
        await update.message.reply_text("⚠️ Hubo un inconveniente al conectar con el simulador del DPE.")
        print(f"Error: {e}")

def main():
    TOKEN = os.environ.get("TELEGRAM_TOKEN")
    if not TOKEN:
        print("Error: Falta la variable TELEGRAM_TOKEN")
        return

    app = Application.builder().token(TOKEN).build()
    app.add_handler(CommandHandler("start", start))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, manejar_mensaje))
    
    print("Bot CFI corregido corriendo con éxito en Railway...")
    app.run_polling()

if __name__ == '__main__':
    main()
