import logging
from telegram import Update
from telegram.ext import ApplicationBuilder,MessageHandler, ContextTypes, CommandHandler
import telegram
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)

accounts = []

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await context.bot.send_message(chat_id=update.effective_chat.id, text="""Bem vindo ao auto cursos bot!
    
    Aqui tem alguns comandos que você pode achar interessante:
    
    \t - /criar_conta
    \t - /login

    ** comandos após login **

    \t - /criar_curso
    \t - /modificar_meus_cursos
    \t - /deletar_cursos
    
    """)


flags = {
    "criando_conta":False,
    "fazendo_login":False,  
        "mandando_username":False,
        "mandando_senha":False,
    "criando_curso":False,
        "mandando_nome_curso":False,
        #etc
}

async def messageHandler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if flags["criando_conta"]:
        if flags["mandando_username"]:
            #handle username testing...
            pass
        if flags["mandando_senha"]:
            #handle password testing...
            pass
    elif flags["fazendo_login"]:
        if flags["mandando_username"]:
            #handle username testing...
            pass
        if flags["mandando_senha"]:
            #handle password testing...
            pass
    
def resetFlags():
    for item in flags.keys():
        flags[item] = False

async def createAccount(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not flags["criando_conta"]:
        resetFlags()
        flags["criando_conta"] = True
        flags["mandando_username"] = True
        await context.bot.send_message(chat_id=update.effective_chat.id, text="Ok! Vamos criar sua conta.\n\nPor favor me diga seu username")
    else:
        await context.bot.send_message(chat_id=update.effective_chat.id, text="Gostaria de começar novamente?")
        #todo


async def handleLogin(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not flags["fazendo_login"]:
        flags["fazendo_login"] = True
        flags["mandando_username"] = True
        await context.bot.send_message(chat_id=update.effective_chat.id, text="Ok! Me diga seu username")

async def checkIfAuthenticated(update: Update):
    #todo
    return True

async def criarCurso(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not checkIfAuthenticated(update=update):
        return
    if not flags["criando_curso"]:
        resetFlags()
        #criar o curso
        flags["criando_curso"] = True





if __name__ == '__main__':
    application = ApplicationBuilder().token('5507439323:AAGiiQ0_vnqIilIRBPRBtGnS54eje4D5xVE').build()
    
    start_handler = CommandHandler('start', start)

    application.add_handler(start_handler)
    application.add_handler(CommandHandler('criar_conta',createAccount))
    application.add_handler(CommandHandler('login',handleLogin))
    
    application.run_polling()