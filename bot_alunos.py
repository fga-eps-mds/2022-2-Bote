


from copy import deepcopy
import logging
from telegram import Update,InlineKeyboardButton
from telegram.ext import ApplicationBuilder,MessageHandler, ContextTypes, CommandHandler,CallbackQueryHandler
import telegram.ext.filters as filters
import telegram
import firebase_admin
from firebase_admin import credentials
from firebase_admin import firestore
from geral import call_database_and_execute,hash_string
from hashlib import sha256

BOT_TOKEN = "5624757690:AAGmsRPmRfEhBnEqKhIfW9pcBjNXsMeDeVY"




logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)


# dicionario para guardar o id da ultima mensagem mandada p/ cada usuário
# serve para evitar mandarmos muitas mensagens
last_messages = {}

# flags por usuário para controlar em qual estágio da conversa ele está
flags_per_user = {}




flags = {
    "entrando_em_curso":False,
        "mandando_codigo":False
}

def make_sure_flags_are_init(user_id):
    """função auxiliar para garantir que não vamos acessar um usuário não existente"""
    if user_id not in flags_per_user:
        flags_per_user[user_id] = deepcopy(flags)




# função auxiliar para evitar mudar uma mensagem muito atrás
def reset_last_message(user_id):
    if user_id in last_messages:
        del last_messages[user_id]

def reset_flags(user_id):
    """função auxiliar para resetar as flags"""
    flags_per_user[user_id] = deepcopy(flags)


async def send_message_on_new_block(update: Update,context: ContextTypes.DEFAULT_TYPE,text:str,buttons = [],parse_mode = ''):
    reset_last_message(update.effective_chat.id)
    await context.bot.send_message(chat_id=update.effective_chat.id,text=text,reply_markup=telegram.InlineKeyboardMarkup(inline_keyboard=buttons),parse_mode=parse_mode)
    

async def send_message_or_edit_last(update: Update,context: ContextTypes.DEFAULT_TYPE,text:str,buttons = [],parse_mode = ''):
    """função auxiliar para enviar uma mensagem mais facilmente ou editar a última se possível"""
    if update.effective_chat.id in last_messages:
        await context.bot.edit_message_text(chat_id=update.effective_chat.id,message_id=last_messages[update.effective_chat.id],text=text,reply_markup=telegram.InlineKeyboardMarkup(inline_keyboard=buttons))
    else:
        message = await context.bot.send_message(chat_id=update.effective_chat.id,text=text,reply_markup=telegram.InlineKeyboardMarkup(inline_keyboard=buttons),parse_mode=parse_mode)
        last_messages[update.effective_chat.id] = message.id


async def start(update: Update,context: ContextTypes.DEFAULT_TYPE):
    make_sure_flags_are_init(update.effective_chat.id)
    dados = call_database_and_execute("SELECT * FROM users WHERE user_id = ?",[update.effective_chat.id])

    if len(dados) == 0:

        await send_message_or_edit_last(update,context,text="Olá! Sou o __nome__, um bot para te auxiliar nos seus cursos!\n\nGostaria de entrar em um curso?",buttons=[
            [
                InlineKeyboardButton(text="sim",callback_data="pegar_codigo_curso")
            ],
            [
                InlineKeyboardButton(text="não",callback_data="nao_deseja_entrar")
            ]
        ])
    else:
        await main_menu(update,context)


async def main_menu(update: Update,context: ContextTypes.DEFAULT_TYPE):
    make_sure_flags_are_init(update.effective_chat.id)
    #TODO
    pass

async def pegar_codigo_curso(update: Update,context: ContextTypes.DEFAULT_TYPE):
    make_sure_flags_are_init(update.effective_chat.id)
    await send_message_or_edit_last(update,context,text="Ok. Por favor me diga o código do curso que você deseja entrar...",buttons=[
        [
            InlineKeyboardButton(text="não tenho código",callback_data="nao_possui_codigo")
        ]
    ])
    flags_per_user[update.effective_chat.id]["entrando_em_curso"] = True
    flags_per_user[update.effective_chat.id]["mandando_codigo"] = True

async def nao_deseja_entrar(update: Update,context: ContextTypes.DEFAULT_TYPE):
    make_sure_flags_are_init(update.effective_chat.id)
    await send_message_or_edit_last(update,context,text="Tudo certo! Se precisar de mim, só mandar uma mensagem com /start nesse chat e eu virei te ajudar!")
    reset_flags(update.effective_chat.id)

async def handler_generic_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    make_sure_flags_are_init(update.effective_chat.id)

    if flags_per_user[update.effective_chat.id]["entrando_em_curso"]:
        if flags_per_user[update.effective_chat.id]["mandando_codigo"]:
            curso_existe = call_database_and_execute("SELECT * FROM cursos WHERE curso_id = ?",[update.effective_message.text])
            if len(curso_existe) == 0:
                await send_message_on_new_block(update,context,text="Não consegui encontrar um curso com esse id, por favor tente novamente...")
                return
            if curso_existe[0]["hash_senha"] != "":
                await send_message_on_new_block(update,context,text="Parece que esse curso precisa de uma senha para entrar, por favor digite a senha para entrar no curso...")
                reset_flags(update.effective_chat.id)
                flags_per_user[update.effective_chat.id]["entrando_em_curso"] = True
                flags_per_user[update.effective_chat.id]["mandando_senha"] = True

                context.user_data['codigo'] = update.effective_message.text
                return
            call_database_and_execute("INSERT INTO alunos_por_curso (aluno_id,curso_id,aulas_completas)",[update.effective_chat.id,update.effective_message.text,""])

            await mostrar_curso(update.effective_message.text,update,context)

        if flags_per_user[update.effective_chat.id]["mandando_senha"]:
            dados_curso = call_database_and_execute("SELECT hash_senha FROM cursos WHERE curso_id = ?",[context.user_data["codigo"]])

            if dados_curso["hash_senha"] == hash_string(update.effective_message.text):
                call_database_and_execute("INSERT INTO alunos_por_curso (aluno_id,curso_id,aulas_completas)",[update.effective_chat.id,context.user_data["codigo"],""])
                await mostrar_curso(context.user_data["codigo"],update,context)
            else:
                await send_message_on_new_block(update,context,text="A senha está incorreta, por favor tente novamente...")
                return

async def mostrar_curso(id_curso: str,update: Update,context: ContextTypes.DEFAULT_TYPE):
    make_sure_flags_are_init(update.effective_chat.id)
    #TODO
    pass

 
if __name__ == '__main__':
    application = ApplicationBuilder().token(BOT_TOKEN).build()
    
    start_handler = CommandHandler('start', start)

    application.add_handler(start_handler)
    application.add_handler(CallbackQueryHandler(pegar_codigo_curso,pattern="pegar_codigo_curso"))
    application.add_handler(CallbackQueryHandler(nao_deseja_entrar,pattern="nao_deseja_entrar"))
    application.add_handler(MessageHandler(filters.TEXT,handler_generic_message))

    application.run_polling()