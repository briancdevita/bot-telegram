import os 
import logging 
from datetime import datetime, timedelta
from dotenv import load_dotenv
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import (
    Application,
    CommandHandler,
    CallbackQueryHandler,
    ContextTypes,
    ConversationHandler,
    MessageHandler,
    filters,
)



from database import (
     create_connection, 
     create_table, 
     save_reservation, 
     check_reservation, 
     delete_reservation, 
     get_user_reservations,
     initialize_database
)


load_dotenv()
BOT_TOKEN = os.getenv("TOKEN")

# Configurar logging
logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s", level=logging.INFO
)
logger = logging.getLogger(__name__)


SELECTING_SERVICE, SELETING_DATE, SELECTING_TIME, CONFIRMING, TYPING_CONTACT = range(5)


reservations = {}

available_services = ["Consulta general", "Asesoria Tecnica", "Soporte"]

available_times = ["09:00", "10:00", "11:00", "14:00", "15:00", "16:00", "17:00", "18:00", "19:00",
]

async def start(update: Update, context: ContextTypes):
    keyboard = [
        [InlineKeyboardButton(service, callback_data=service)]
        for service in available_services
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    await update.message.reply_text(
        "👋 ¡Bienvenido al Sistema de Reservas! \n\n"
        "Por favor, selecciona el servicio que deseas reservar:", 
        reply_markup=reply_markup
        )
    return SELECTING_SERVICE


async def select_service(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Maneja la seleccion de servicio y muestra los horarios disponibles"""

    query = update.callback_query
    await query.answer()

    select_service = query.data
    context.user_data["service"] = select_service


    dates = []

    for i in range(1, 6):
        date = datetime.now() + timedelta(days=i)
        dates.append(date.strftime("%d-%m-%Y"))

        keyboard = [
            [InlineKeyboardButton(date, callback_data=date)] for date in dates
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)

        await query.message.reply_text(
            f"Has seleccionado: {select_service}\n\n"
            "Por favor, selecciona una fecha para tu reserva:",
            reply_markup=reply_markup,
        )

        return SELETING_DATE
    
async def selected_time(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:

    """Maneja la selecciond e hora y solicitia informacion de contacto"""

    query = update.callback_query
    await query.answer()

    selected_date = query.data
    context.user_data["date"] = selected_date

    keyboard = [
        [InlineKeyboardButton(time, callback_data=time)]
        for time in available_times
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)

    await query.edit_message_text(
        f"Has seleccionado: {selected_date}\n\n"
        "Por favor, selecciona una hora para tu reserva:",
        reply_markup=reply_markup,
    )

    return SELECTING_TIME

async def save_contact(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Guarda la informacion de contacto y confirma la reserva"""

    user_name = update.message.text 
    context.user_data["contact"] = user_name


    reservation_id = F"RES-{datetime.now().strftime('%Y%m%d%H%M%S')}"
    context.user_data["reservation_id"] = reservation_id




    # Guardar la reserva en la base de datos
    db_result = save_reservation(
        id = reservation_id,
        user_id = update.effective_user.id,
        service = context.user_data["service"],
        date = context.user_data["date"],
        time = context.user_data["time"],
        contact= user_name,
    )


    

    if db_result:
        logger.info(f"Reserva guardada en la base de datos: {reservation_id}")
    else:
        logger.error(f"No se pudo guardar la reserva en la base de datos: {reservation_id}")

    keyboard = [
        [
            InlineKeyboardButton("Confirmar ✅", callback_data="confirm"),
            InlineKeyboardButton("Cancelar ❌", callback_data="cancel")
        ]
    ]

    reply_markup = InlineKeyboardMarkup(keyboard)

    await update.message.reply_text(
        f"📝 Resumen de tu reserva:\n\n"
        f"🆔 ID de Reserva: {reservation_id}\n"
        f"🧩 Servicio: {context.user_data['service']}\n"
        f"📅 Fecha: {context.user_data['date']}\n"
        f"🕒 Hora: {context.user_data['time']}\n"
        f"👤 Contacto: {context.user_data['contact']}\n\n"
        "Por favor, confirma tu reserva:",
        reply_markup=reply_markup,
        parse_mode="Markdown",
    )
    return CONFIRMING


async def confirm_reservation(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Confirma la reserva y envia un mensaje de confirmacion"""

    query = update.callback_query
    await query.answer()

    if query.data == "confirm":
        await query.edit_message_text(
            f"¡Reserva confirmada! 🎉\n\n"
            f"Tu reserva con ID {context.user_data['reservation_id']} ha sido confirmada.\n"
            f"Te esperamos el {context.user_data['date']} a las {context.user_data['time']}.\n"
            f"Para cancelartu reserva usa el comando /cancelar seguido de tu ID de reserva."
            "Para hacer una nueva reserva usa el comando /start."

        )

    else :
        if context.user_data["reservation_id"] in reservations:
            del reservations[context.user_data("reservation_id")]

        await query.edit_message_text(
            "Reserva cancelada. Para hacer una nueva reserva usa el comando /start."

        )

        context.user_data.clear()
        return ConversationHandler.END
    
async def cancel_reservation(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:

    """Cancela la reserva y envia un mensaje de cancelacion"""

    if not context.args:
        await update.message.reply_text(
            "Por favor, ingresa el ID de la reserva que deseas cancelar."
            "Ejemplo: /cancelar RES-0001"
        )
        return
    

    reservation_id = context.args[0]
    print("reservation_id", context.user_data['reservation_id'])


    if check_reservation(reservation_id):
        if delete_reservation(reservation_id):
            await update.message.reply_text(
                f"Reserva {reservation_id} cancelada."
            )
        else:
            await update.message.reply_text(
                "No se pudo cancelar la reserva.")
    else:
        await update.message.reply_text(
            "No se encontro ninguna reserva con ese ID."
        )



async def list_reservations(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Lista las reservas del usuario"""

    user_id = update.effective_user.id
    user_reservations = get_user_reservations(user_id)

    if  user_reservations:
        message = "📋* Tus reservas:*\n\n"

        for reservation in user_reservations:

            message += (
                f"🆔 ID de Reserva: {reservation['id']}\n"
                f"🧩 Servicio: {reservation['service']}\n"
                f"📅 Fecha: {reservation['date']}\n"
                f"🕒 Hora: {reservation['time']}\n"
                f"👤 Contacto: {reservation['contact']}\n\n"
            )

    if user_reservations:
        await update.message.reply_text(
            message, parse_mode="Markdown"
        )
    else:
        await update.message.reply_text("No tienes reservas.")


async def help_command (update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Envia un mensaje de ayuda al usuario"""

    await update.message.reply_text(
        "Este es un sistema de reservas. Puedes usar los siguientes comandos:\n\n"
        "/start - Inicia el sistema de reservas\n"
        "/cancelar - Cancela una reserva\n"
        "/reservas - Muestra tus reservas"
    )

async def select_contact_info(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Solicita la informacion de contacto al usuario"""

    query = update.callback_query
    await query.answer()

    selected_time = query.data
    context.user_data["time"] = selected_time

    await query.edit_message_text(
        f"Has seleccionado: {selected_time}\n\n"
        "Por favor, ingresa tu nombre completo:"
    )

    return TYPING_CONTACT


def main() -> None:
    """Configura el bot y lo ejecuta"""
 
    if not  initialize_database():
        logger.info("NO SE PUDO CREAR LA BASE DE DATOS")
    application = Application.builder().token(BOT_TOKEN).build()

    conv_handler = ConversationHandler(
        entry_points=[CommandHandler("start", start)],
        states={
       
            SELECTING_SERVICE: [
                CallbackQueryHandler(select_service),
            ],
            SELETING_DATE: [
                CallbackQueryHandler(selected_time),
            ],
            SELECTING_TIME: [
                CallbackQueryHandler(select_contact_info),
            ],
            TYPING_CONTACT: [
               MessageHandler(filters.TEXT & ~filters.COMMAND, save_contact),
            ],
            CONFIRMING: [
                CallbackQueryHandler(confirm_reservation),
            ],
        },
        fallbacks=[CommandHandler("cancelar", cancel_reservation), CommandHandler("reservas", list_reservations)],
    )

    application.add_handler(conv_handler)
    application.add_handler(CommandHandler("ayuda", help_command))

    # Solo cambiado run() por run_polling()
    application.run_polling()

if __name__ == "__main__":
    main()












