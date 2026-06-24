import os
from telegram import Update, ReplyKeyboardMarkup
from telegram.ext import Application, CommandHandler, MessageHandler, filters, ContextTypes
from google import genai
from google.genai import types

# Inicializamos el cliente de Gemini
ai_client = genai.Client()

# Estructura oficial del ACS de CFI (XIV Áreas de Operación)
ESTRUCTURA_ACS = {
    "I. Fundamentals of Instructing": [
        "Task A: Human Behavior", "Task B: The Learning Process",
        "Task C: Effective Communication", "Task D: The Teaching Process",
        "Task E: Assessment", "Task F: Flight Instructor Characteristics",
        "Task G: Elements of Effective Instruction"
    ],
    "II. Technical Subject Areas": [
        "Task A: Aeromedical Factors", "Task B: Visual Inspection & Airworthiness",
        "Task C: Principles of Flight", "Task D: Airplane Flight Controls",
        "Task E: Airplane Systems", "Task F: Navigation & Flight Planning",
        "Task G: Night Operations", "Task H: High-Altitude Operations",
        "Task I: Regulations & Endorsements"
    ],
    "III. Preflight Preparation": [
        "Task A: Pilot Certificates & Documents", "Task B: Weather Information",
        "Task C: Operation of Systems", "Task D: Performance & Limitations",
        "Task E: Airworthiness Requirements"
    ],
    "IV. Preflight Lesson on a Maneuver": [
        "Task A: Maneuver Lesson Description"
    ],
    "V. Airport Operations": [
        "Task A: Radio Communications", "Task B: Airport Markings & Lighting",
        "Task C: Shotfield/Softfield Operations"
    ],
    "VI. Takeoffs, Landings, and Go-Arounds": [
        "Task A: Normal Takeoff & Climb", "Task B: Crosswind Takeoff & Climb",
        "Task C: Short-Field Takeoff & Climb", "Task D: Soft-Field Takeoff & Climb",
        "Task E: Normal Approach & Landing", "Task F: Slip to a Landing",
        "Task G: Go-Around / Rejected Landing"
    ],
    "VII. Performance Maneuvers": [
        "Task A: Steep Turns", "Task B: Steep Spirals",
        "Task C: Chandelles", "Task D: Lazy Eights"
    ],
    "VIII. Ground Reference Maneuvers": [
        "Task A: Rectangular Course", "Task B: S-Turns",
        "Task C: Turns Around a Point"
    ],
    "IX. Navigation": [
        "Task A: Pilotage & Dead Reckoning", "Task B: Navigation Systems",
        "Task C: Diversion / Lost Procedures"
    ],
    "X. Slow Flight and Stalls": [
        "Task A: Maneuvering in Slow Flight", "Task B: Power-On Stalls",
        "Task C: Power-Off Stalls", "Task D: Accelerated Stalls",
        "Task E: Spin Awareness"
    ],
    "XI. Emergency Operations": [
        "Task A: Emergency Approach & Landing", "Task B: Systems & Equipment Malfunctions",
        "Task C: Emergency Descent"
    ],
    "XII. Multiengine Operations": [
        "Task A: Engine Failure After Takeoff", "Task B: VMC Demonstration",
        "Task C: One-Engine Inoperative Approach"
    ],
    "XIII. Postflight Procedures": [
        "Task A: Postflight Procedures"
    ],
    "XIV. Plan of Action": [
        "Task A: Developing a Plan of Action"
    ]
}

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

# Instrucción del sistema moldeada para el método socrático estricto
INSTRUCCION_SOCRATICA = (
    "Actuarás rigurosamente como un Tutor Socrático Experto para un candidato a Instructor de Vuelo (CFI) de la FAA. "
    "Tu única base de conocimiento son los manuales oficiales de la FAA (PHAK, AIH, AFH y el ACS de CFI).\n\n"
    "MÉTODO SOCRÁTICO ESPECÍFICO:\n"
    "1. NO des respuestas directas, resúmenes ni explicaciones completas de inmediato.\n"
    "2. Tu objetivo es guiar al estudiante mediante preguntas consecutivas de seguimiento para que él mismo descubra y deduzca el concepto correcto del manual.\n"
    "3. Adapta tu siguiente pregunta basándote críticamente en el error o acierto de la respuesta anterior del alumno.\n"
    "4. Mantén un tono desafiante pero profesional, digno de un instructor avanzado."
)

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Inicializa la sesión y muestra el Menú Principal de Áreas"""
    context.user_data.clear() # Limpiamos cualquier estado previo
    reply_markup = ReplyKeyboardMarkup(MENU_PRINCIPAL, resize_keyboard=True)
    await update.message.reply_text(
        "🧠 **Tutor Socrático de CFI - FAA** 🧠\n\n"
        "Selecciona un **Área de Operación** para desplegar sus tareas. Al elegir una tarea, iniciaremos una guía interactiva "
        "de **5 preguntas socráticas** para ayudarte a dominar el estándar.",
        reply_markup=reply_markup,
        parse_mode="Markdown"
    )

async def mostrar_submenu_tareas(update: Update, context: ContextTypes.DEFAULT_TYPE, area: str):
    """Muestra las tareas correspondientes al área seleccionada con opción de regresar"""
    context.user_data["area_actual"] = area
    context.user_data["task_actual"] = None
    context.user_data["contador_preguntas"] = 0
    
    tareas = ESTRUCTURA_ACS[area]
    botones_tareas = [[tarea] for tarea in tareas]
    botones_tareas.append(["⬅️ Volver al Menú de Áreas"]) # Botón de escape al menú principal
    
    reply_markup = ReplyKeyboardMarkup(botones_tareas, resize_keyboard=True)
    await update.message.reply_text(
        f"📂 **{area}**\n\nSelecciona la **Task** que deseas practicar hoy o regresa al menú principal:",
        reply_markup=reply_markup,
        parse_mode="Markdown"
    )

async def manejar_mensaje(update: Update, context: ContextTypes.DEFAULT_TYPE):
    texto = update.message.text
    
    # 1. Control de navegación global
    if texto == "🔄 Reset / Volver al Inicio" or texto == "⬅️ Volver al Menú de Áreas":
        await start(update, context)
        return

    # 2. Control de salida durante el cuestionario activo
    if texto == "❌ Abandonar Tarea Actual":
        area_activa = context.user_data.get("area_actual")
        if area_activa:
            await update.message.reply_text("🔄 Sesión socrática interrumpida.")
            await mostrar_submenu_tareas(update, context, area_activa)
        else:
            await start(update, context)
        return

    # 3. El usuario selecciona un Área de Operación en el Menú Principal
    if texto in ESTRUCTURA_ACS:
        await mostrar_submenu_tareas(update, context, texto)
        return

    # 4. El usuario selecciona una Task específica dentro de un área
    area_activa = context.user_data.get("area_actual")
    task_activa = context.user_data.get("task_actual")

    if area_activa and texto in ESTRUCTURA_ACS[area_activa] and not task_activa:
        context.user_data["task_actual"] = texto
        context.user_data["contador_preguntas"] = 1
        
        # Teclado de control durante el cuestionario interactivo
        teclado_ejecucion = [["❌ Abandonar Tarea Actual"]]
        reply_markup = ReplyKeyboardMarkup(teclado_ejecucion, resize_keyboard=True)
        
        await update.message.reply_text(
            f"🚀 Iniciando tutoría socrática para:\n`{texto}`\n\n"
            f"Pregunta **1 de 5**...", 
            reply_markup=reply_markup, parse_mode="Markdown"
        )
        
        prompt_inicial = (
            f"El estudiante seleccionó el '{area_activa}', específicamente la '{texto}'. "
            f"Haz la primera pregunta socrática introductoria del caso (Pregunta 1 de 5) para guiarlo a comprender esta sección según la FAA."
        )
        await enviar_a_gemini(update, prompt_inicial)
        return

    # 5. El usuario está respondiendo en medio de las 5 preguntas socráticas
    if area_activa and task_activa:
        contador = context.user_data.get("contador_preguntas", 0)
        contador += 1
        context.user_data["contador_preguntas"] = contador

        if contador <= 5:
            prompt_seguimiento = (
                f"Estamos en la sesión socrática de '{task_activa}'. Esta es la interacción número {contador} de 5. "
                f"El estudiante respondió: '{texto}'. Evalúa su razonamiento sin darle la respuesta final directamente, "
                f"y genera la siguiente pregunta socrática guía que lo acerque al estándar correcto de los manuales de la FAA."
            )
            await enviar_a_gemini(update, prompt_seguimiento)
        else:
            # Fin de las 5 preguntas: El modelo genera la conclusión/retroalimentación final
            prompt_final = (
                f"Hemos llegado al final de las 5 preguntas socráticas para '{task_activa}'. "
                f"El alumno envió su última respuesta: '{texto}'. Haz el cierre de la sesión, resume brevemente "
                f"las fortalezas o debilidades que demostró en sus respuestas y cítale los capítulos específicos de los manuales de la FAA "
                f"(PHAK, AIH o AFH) que debe repasar para consolidar el estándar."
            )
            await enviar_a_gemini(update, prompt_final)
            
            # Devolver automáticamente al submenú de tareas de esa área operativa
            await update.message.reply_text("✨ Sesión finalizada con éxito. Volviendo al listado de tareas...")
            await mostrar_submenu_tareas(update, context, area_activa)
        return

    await update.message.reply_text("Por favor, selecciona una opción válida del menú inferior para iniciar.")

async def enviar_a_gemini(update: Update, prompt: str):
    try:
        response = ai_client.models.generate_content(
            model='gemini-2.5-flash',
            contents=prompt,
            config=types.GenerateContentConfig(
                system_instruction=INSTRUCCION_SOCRATICA,
                temperature=0.5
            )
        )
        await update.message.reply_text(response.text)
    except Exception as e:
        await update.message.reply_text("⚠️ Error temporal en el motor del tutor socrático.")
        print(f"Error: {e}")

def main():
    TOKEN = os.environ.get("TELEGRAM_TOKEN")
    if not TOKEN:
        print("Error: Falta la variable TELEGRAM_TOKEN")
        return

    app = Application.builder().token(TOKEN).build()
    app.add_handler(CommandHandler("start", start))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, manejar_mensaje))
    
    print("Bot Tutor Socrático jerárquico corriendo con éxito en Railway...")
    app.run_polling()

if __name__ == '__main__':
    main()
