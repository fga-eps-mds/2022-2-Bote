


import logging
from telegram import Update,InlineKeyboardButton
from telegram.ext import ApplicationBuilder,MessageHandler, ContextTypes, CommandHandler,CallbackQueryHandler
import telegram.ext.filters as filters
import telegram
import firebase_admin
from firebase_admin import credentials
from firebase_admin import firestore


BOT_TOKEN = "5624757690:AAGmsRPmRfEhBnEqKhIfW9pcBjNXsMeDeVY"



logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)

async def start(update: Update,context: ContextTypes.DEFAULT_TYPE):
    await context.bot.send_message(text="Olá, como posso te ajudar?",chat_id=update.effective_chat.id,reply_markup=telegram.InlineKeyboardMarkup(inline_keyboard=[
        [
            InlineKeyboardButton(text='Ver meus cursos',callback_data='cursos')
        ]
    ]))
    

    pass


if __name__ == '__main__':
    application = ApplicationBuilder().token(BOT_TOKEN).build()
    
    start_handler = CommandHandler('start', start)

    application.add_handler(start_handler)
    
    application.run_polling()