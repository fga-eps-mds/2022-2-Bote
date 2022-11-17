import logging
from telegram import Update,InlineKeyboardButton
from telegram.ext import ApplicationBuilder,MessageHandler, ContextTypes, CommandHandler,CallbackQueryHandler
import telegram.ext.filters as filters
import telegram


logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)

accounts = []
usuario_professor = False

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if usuario_professor:
        await context.bot.send_message(chat_id=update.effective_chat.id, text="""Bem vindo ao auto cursos bot!
        
        o que você deseja fazer?

        """,reply_markup=telegram.InlineKeyboardMarkup(inline_keyboard=[
        [
            telegram.InlineKeyboardButton(text="entrar",callback_data='entrar'),

        ],
        [
            telegram.InlineKeyboardButton(text="criar conta",callback_data='criar_conta')

        ]
        ]))
    else:
        await context.bot.send_message(chat_id=update.effective_chat.id, text="""Bem vindo ao auto cursos bot!

        o que você deseja fazer?

        """,reply_markup=telegram.InlineKeyboardMarkup(inline_keyboard=[
        [
            telegram.InlineKeyboardButton(text="ver seus cursos",callback_data='entrar'),

        ]
        ]))




flags = {
    "criando_conta":False,
    "fazendo_login":False,  
        "mandando_username":False,
        "mandando_senha":False,
    "criando_curso":False,
        "mandando_nome_curso":False,
        #etc
}


async def mostrarMenuPrincipal(update: Update,context: ContextTypes.DEFAULT_TYPE):
    await context.bot.send_message(chat_id=update.effective_chat.id,text='O que você deseja fazer?',reply_markup=telegram.InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(text="criar curso"),
            ],
            [
                InlineKeyboardButton(text='ver seus cursos')
            ]
        ]
    ))


async def messageHandler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    print('calling message handler!')
    print(flags)
    if flags['criando_conta'] == True:
        if flags["mandando_username"]:
            print('mandando username!')
            
            #TODO: testar se ja tem username assim e salvar username 
            flags["mandando_username"] = False
            flags["mandando_senha"] = True
            
            await context.bot.send_message(chat_id=update.effective_chat.id,text='me diga sua senha...')
            return
        if flags["mandando_senha"]:
            #TODO: salvar senha e mandar pro DB
            print('mandando senha!')
            await context.bot.send_message(chat_id=update.effective_chat.id,text='obrigado por criar sua conta!')
            resetFlags()
            start(update,context)
            return
    if flags['fazendo_login']:
        if flags['mandando_username']:
            print('mandando username!')
            
            #TODO: fazer login
            flags["mandando_username"] = False
            flags["mandando_senha"] = True
            
            await context.bot.send_message(chat_id=update.effective_chat.id,text='me diga sua senha...')
            return
        if flags['mandando_senha']:
            print('mandando username!')
            
            #TODO: fazer login
            resetFlags()
            mostrarMenuPrincipal(update,context)

            return




    
def resetFlags():
    for item in flags.keys():
        flags[item] = False



async def criarCurso(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not flags["criando_curso"]:
        resetFlags()
        #criar o curso
        flags["criando_curso"] = True


async def CriarContaCallback(update: Update,context: ContextTypes.DEFAULT_TYPE):
    resetFlags()
    flags["criando_conta"] = True
    await context.bot.send_message(chat_id=update.effective_chat.id,text='me diga o username que você deseja utilizar...')
    flags['mandando_username'] = True


async def EntrarCallback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    resetFlags()
    flags["fazendo_login"] = True
    await context.bot.send_message(chat_id=update.effective_chat.id,text='me diga seu username...')
    flags['mandando_username'] = True
    

if __name__ == '__main__':
    application = ApplicationBuilder().token('5507439323:AAGiiQ0_vnqIilIRBPRBtGnS54eje4D5xVE').build()
    
    start_handler = CommandHandler('start', start)

    application.add_handler(start_handler)
    application.add_handler(MessageHandler(callback=messageHandler,filters=filters.TEXT))
    application.add_handler(CallbackQueryHandler(callback=EntrarCallback,pattern='entrar'))
    application.add_handler(CallbackQueryHandler(callback=CriarContaCallback,pattern='criar_conta'))
    
    application.run_polling()