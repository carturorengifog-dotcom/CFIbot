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
    "3. Adapta tu siguiente pregunta basándote críticamente en el error o acierto de la respuesta anterior del alumno, "
    "tomando en cuenta TODO el historial de la conversación para detectar patrones, avances y lagunas de conocimiento.\n"
    "4. Mantén un tono desafiante pero profesional, digno de un instructor avanzado.\n"
    "5. Nunca repitas una pregunta que ya hayas formulado anteriormente en la misma sesión."
)


def limpiar_historial(context: ContextTypes.DEFAULT_TYPE):
    """Limpia el historial de conversación de Gemini y resetea el estado de la sesión."""
    context.user_data["historial_gemini"] = []  # Lista de types.Content
    context.user_data["task_actual"] = None
    context.user_data["contador_preguntas"] = 0


async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Inicializa la sesión y muestra el Menú Principal de Áreas."""
    context.user_data.clear()
    context.user_data["historial_gemini"] = []
    reply_markup = ReplyKeyboardMarkup(MENU_PRINCIPAL, resize_keyboard=True)
    await update.message.reply_text(
        "🧠 **Tutor Socrático de CFI - FAA** 🧠\n\n"
        "Selecciona un **Área de Operación** para desplegar sus tareas. Al elegir una tarea, iniciaremos una guía interactiva "
        "de **5 preguntas socráticas** para ayudarte a dominar el estándar.",
        reply_markup=reply_markup,
        parse_mode="Markdown"
    )


async def mostrar_submenu_tareas(update: Update, context: ContextTypes.DEFAULT_TYPE, area: str):
    """Muestra las tareas del área seleccionada y limpia el historial de la sesión anterior."""
    context.user_data["area_actual"] = area
    limpiar_historial(context)

    tareas = ESTRUCTURA_ACS[area]
    botones_tareas = [[tarea] for tarea in tareas]
    botones_tareas.append(["⬅️ Volver al Menú de Áreas"])

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
        # El historial ya fue limpiado en mostrar_submenu_tareas; lo confirmamos vacío
        context.user_data.setdefault("historial_gemini", [])

        teclado_ejecucion = [["❌ Abandonar Tarea Actual"]]
        reply_markup = ReplyKeyboardMarkup(teclado_ejecucion, resize_keyboard=True)

        await update.message.reply_text(
            f"🚀 Iniciando tutoría socrática para:\n`{texto}`\n\n"
            f"Pregunta **1 de 5**...",
            reply_markup=reply_markup,
            parse_mode="Markdown"
        )

        prompt_inicial = (
            f"El estudiante seleccionó el '{area_activa}', específicamente la '{texto}'. "
            f"Haz la primera pregunta socrática introductoria (Pregunta 1 de 5) para guiarlo "
            f"a comprender esta sección según los estándares de la FAA."
        )
        await enviar_a_gemini(update, context, prompt_inicial)
        return

    # 5. El usuario está respondiendo dentro de la sesión socrática activa
    if area_activa and task_activa:
        contador = context.user_data.get("contador_preguntas", 0)
        contador += 1
        context.user_data["contador_preguntas"] = contador

        if contador <= 5:
            # El historial acumulado le da a Gemini todo el contexto previo;
            # el prompt solo necesita indicar el número de interacción.
            prompt_seguimiento = (
                f"Interacción {contador} de 5 en la sesión sobre '{task_activa}'. "
                f"El estudiante acaba de responder: '{texto}'. "
                f"Basándote en TODO el historial de esta sesión, evalúa su razonamiento "
                f"sin revelar la respuesta final y formula la siguiente pregunta socrática "
                f"que lo acerque al estándar correcto de los manuales de la FAA."
            )
            await enviar_a_gemini(update, context, prompt_seguimiento)
        else:
            # Cierre: el modelo tiene acceso al historial completo para la retroalimentación final
            prompt_final = (
                f"Hemos llegado al final de las 5 preguntas socráticas para '{task_activa}'. "
                f"La última respuesta del alumno fue: '{texto}'. "
                f"Revisando TODO el historial de esta sesión, haz el cierre: resume las fortalezas "
                f"y debilidades que demostró a lo largo de los intercambios y cítale los capítulos "
                f"específicos de los manuales de la FAA (PHAK, AIH o AFH) que debe repasar para "
                f"consolidar el estándar."
            )
            await enviar_a_gemini(update, context, prompt_final)

            await update.message.reply_text("✨ Sesión finalizada con éxito. Volviendo al listado de tareas...")
            await mostrar_submenu_tareas(update, context, area_activa)
        return

    await update.message.reply_text("Por favor, selecciona una opción válida del menú inferior para iniciar.")


async def enviar_a_gemini(update: Update, context: ContextTypes.DEFAULT_TYPE, prompt: str):
    """
    Envía el prompt a Gemini manteniendo el historial completo de la sesión.
    El historial se almacena en context.user_data['historial_gemini'] como una
    lista de types.Content con roles 'user' y 'model', que se pasa en cada llamada.
    """
    historial: list = context.user_data.setdefault("historial_gemini", [])

    # Añadimos el turno del usuario al historial ANTES de llamar a la API
    historial.append(
        types.Content(role="user", parts=[types.Part(text=prompt)])
    )

    try:
        response = ai_client.models.generate_content(
            model="gemini-2.5-flash",
            contents=historial,          # <-- historial completo multi-turn
            config=types.GenerateContentConfig(
                system_instruction=INSTRUCCION_SOCRATICA,
                temperature=0.5
            )
        )
        respuesta_texto = response.text

        # Añadimos la respuesta del modelo al historial para el siguiente turno
        historial.append(
            types.Content(role="model", parts=[types.Part(text=respuesta_texto)])
        )

        await update.message.reply_text(respuesta_texto)

    except Exception as e:
        # Si hubo error, retiramos el turno de usuario que ya habíamos añadido
        # para no dejar el historial en un estado inconsistente
        if historial and historial[-1].role == "user":
            historial.pop()
        await update.message.reply_text("⚠️ Error temporal en el motor del tutor socrático.")
        print(f"Error Gemini: {e}")


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
