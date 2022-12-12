import logging
from telegram import Update,InlineKeyboardButton
from telegram.ext import ApplicationBuilder,MessageHandler, ContextTypes, CommandHandler,CallbackQueryHandler
import telegram.ext.filters as filters
import telegram
from telegram.constants import ParseMode
import sqlite3 as sql
import os
from hashlib import sha256
from typing import List



# definindo como o log vai ser salvo
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)


last_messages = {}
flags_per_user = {}
temp_dados_curso = {}


#função para auxiliar no uso do banco de dados SQL
def call_database_and_execute(statement,parameters = []) -> List[sql.Row]:
    db = sql.connect("database.db")
    db.row_factory = sql.Row
    data = db.cursor().execute(statement,parameters)
    
    final_data =  data.fetchall()
    db.commit()
    db.close()
    return final_data

flags = {
    "criando_curso":False,
        "mandando_nome_curso":False,
        "mandando_descricao_curso":False,
        "mandando_senha_curso":False
        #etc
}

def make_sure_flags_are_init(user_id):
    if user_id not in flags_per_user:
        flags_per_user[user_id] = flags

def resetFlags(user_id):
    print('calling reset flags!')
    flags_per_user[user_id] = flags
    if user_id in temp_dados_curso:
        del temp_dados_curso[user_id]
    
def resetLastMessage(user_id):
    if user_id in last_messages:
        del last_messages[user_id]

async def send_message_or_edit_last(update: Update,context: ContextTypes.DEFAULT_TYPE,text:str,buttons = [],parse_mode = ''):
    if update.effective_chat.id in last_messages:
        await context.bot.edit_message_text(chat_id=update.effective_chat.id,message_id=last_messages[update.effective_chat.id],text=text,reply_markup=telegram.InlineKeyboardMarkup(inline_keyboard=buttons))
    else:
        message = await context.bot.send_message(chat_id=update.effective_chat.id,text=text,reply_markup=telegram.InlineKeyboardMarkup(inline_keyboard=buttons),parse_mode=parse_mode)
        last_messages[update.effective_chat.id] = message.id

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    
    data = call_database_and_execute("SELECT * FROM users WHERE user_id = ?",(update.effective_user.id,))
    resetFlags(update.effective_chat.id)
    resetLastMessage(update.effective_chat.id)
    message = """Bem vindo ao auto cursos bot!
    
"""
    message += "Sou um bot para criar e administrar cursos pelo Telegram!\n\n"
    if len(data) == 0:
        message += "Gostaria de criar um curso?"
        call_database_and_execute("INSERT INTO users (user_id) VALUES (?)",[update.effective_chat.id])
        await send_message_or_edit_last(update,context,text=message,buttons=[
        [
            telegram.InlineKeyboardButton(text="Sim",callback_data='criar_curso'),
        ],
        [
            telegram.InlineKeyboardButton(text="Não",callback_data='nao_deseja_criar_curso')
        ]
        ])
    else:

        await mostrarMenuPrincipal(message,update,context)






async def mostrarMenuPrincipal(message: str,update: Update,context: ContextTypes.DEFAULT_TYPE):
    numero_de_cursos = call_database_and_execute("SELECT COUNT(*) FROM cursos WHERE dono_id = ?",[update.effective_chat.id])[0]
    buttons = [
            [
                InlineKeyboardButton(text="criar novo curso",callback_data="criar_curso"),
            ]
        ]
    print(numero_de_cursos["COUNT(*)"])
    if numero_de_cursos["COUNT(*)"] > 0:
        buttons.append([
                InlineKeyboardButton(text='ver seus cursos',callback_data="ver_cursos")
        ])

    await send_message_or_edit_last(update,context,text=message + "Como posso ajudar hoje?",buttons=buttons)



async def messageHandler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    print('calling message handler!')
    make_sure_flags_are_init(update.effective_chat.id)

    if flags_per_user[update.effective_chat.id]['criando_curso']:
        if flags_per_user[update.effective_chat.id]["mandando_nome_curso"]:
            temp_dados_curso[update.effective_chat.id]['nome'] = update.effective_message.text
            await context.bot.send_message(chat_id=update.effective_chat.id,text="Ok! Agora me diga uma breve descrição do seu curso",reply_markup=telegram.InlineKeyboardMarkup(
                inline_keyboard=[
                    [
                        InlineKeyboardButton("voltar ao menu",callback_data="voltar_ao_menu")
                    ]
                ]
            ))
            flags_per_user[update.effective_chat.id]["mandando_nome_curso"] = False
            flags_per_user[update.effective_chat.id]["mandando_descricao_curso"] = True
            resetLastMessage(update.effective_chat.id)
            return
        if flags_per_user[update.effective_chat.id]["mandando_descricao_curso"]:
            temp_dados_curso[update.effective_chat.id]['descricao'] = update.effective_message.text
            flags_per_user[update.effective_chat.id]["mandando_descricao_curso"] = False
            flags_per_user[update.effective_chat.id]["mandando_senha_curso"] = True
            await context.bot.send_message(chat_id=update.effective_chat.id,text="Ok! Agora me diga a senha para os alunos entrarem no seu curso",reply_markup=telegram.InlineKeyboardMarkup(
                inline_keyboard=[
                    [
                        InlineKeyboardButton("não desejo colocar",callback_data="nao_deseja_colocar_senha_em_curso")
                    ],
                    [
                        InlineKeyboardButton("voltar ao menu",callback_data="voltar_ao_menu")
                    ]
                ]
            ))
            resetLastMessage(update.effective_chat.id)
            return
        if flags_per_user[update.effective_chat.id]["mandando_senha_curso"]:
            temp_dados_curso[update.effective_chat.id]['senha'] = update.effective_message.text
            curso_id = sha256((str(update.effective_chat.id) + "curso" + temp_dados_curso[update.effective_chat.id]['nome']).encode('utf-8')).hexdigest()[:15]
            call_database_and_execute("INSERT INTO cursos (nome,descricao,hash_senha,dono_id,id) VALUES (?,?,?,?,?)",[
                temp_dados_curso[update.effective_chat.id]["nome"],
                temp_dados_curso[update.effective_chat.id]["descricao"],
                sha256(temp_dados_curso[update.effective_chat.id]["senha"].encode('utf-8')).hexdigest(),
                update.effective_chat.id,
                curso_id
            ])
            resetFlags(update.effective_chat.id)
            resetLastMessage(update.effective_chat.id)
            await menuCurso(curso_id,update,context)
            return
    


async def menuCurso(id_curso: str,update: Update,context: ContextTypes.DEFAULT_TYPE):
    dados_curso = call_database_and_execute("SELECT * FROM cursos WHERE id = ?",[id_curso])
    buttons = [
            [
                InlineKeyboardButton(text="ver id do curso",callback_data=f"receber_id_curso {dados_curso[0]['id']}")
            ],
            [
                InlineKeyboardButton(text="editar nome",callback_data="editar_nome_curso")
            ],
            [
                InlineKeyboardButton(text="editar descrição",callback_data="editar_descricao_curso")
            ],
            [
                InlineKeyboardButton(text="ver aulas cadastradas",callback_data="editar_aulas")
            ],
            [
                InlineKeyboardButton(text="voltar ao menu",callback_data="voltar_ao_menu")
            ],
        ]
    text = f"O que você gostaria de editar?\n\nCurso atual: {dados_curso[0]['nome']}\n\nDescrição do curso: {dados_curso[0]['descricao']}"
    await send_message_or_edit_last(update,context,text=text,buttons=buttons,parse_mode=ParseMode.MARKDOWN_V2)


async def verCursos(update: Update,context: ContextTypes.DEFAULT_TYPE):
    data = call_database_and_execute("SELECT nome,id FROM cursos WHERE dono_id = ?",[update.effective_chat.id])
    print(list(map(lambda i: len(f'ver_curso_especifico {i["id"]}'.encode('utf-8')),data)))
    buttons = [[InlineKeyboardButton(text=i['nome'],callback_data=f'ver_curso_especifico {i["id"]}')] for i in data]
    buttons.append([InlineKeyboardButton(text="voltar ao menu",callback_data='voltar_ao_menu')])
    await send_message_or_edit_last(update,context,text="Qual curso você deseja editar?",buttons=buttons)
        

async def criarCurso(update: Update, context: ContextTypes.DEFAULT_TYPE):
    make_sure_flags_are_init(update.effective_chat.id)
    if update.effective_chat.id in last_messages:
        await context.bot.edit_message_text(chat_id=update.effective_chat.id,message_id=last_messages[update.effective_chat.id],text="Ok, vamos criar seu curso!\n\nQual título você quer em seu curso?",reply_markup=telegram.InlineKeyboardMarkup(
            inline_keyboard=[
                [
                    InlineKeyboardButton("voltar ao menu",callback_data="voltar_ao_menu")
                ]
            ]
        ))
        flags_per_user[update.effective_chat.id]['criando_curso'] = True
        flags_per_user[update.effective_chat.id]['mandando_nome_curso'] = True
        temp_dados_curso[update.effective_chat.id] = {"nome":"","descricao":"","senha":""}


async def naoDesejaCriarCurso(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_chat.id in last_messages:
        await context.bot.edit_message_text(chat_id=update.effective_chat.id,message_id=last_messages[update.effective_chat.id],text="Tudo certo!\n\nQuando quiser utilizar meus serviços digite /start nesse chat e eu virei te ajudar!\n\nTenha um bom dia :D")
    else:
        await context.bot.send_message(chat_id=update.effective_chat.id,text="Tudo certo!\n\nQuando quiser utilizar meus serviços digite /start nesse chat e eu virei te ajudar!\n\nTenha um bom dia :D")

async def voltarAoMenu(update: Update, context: ContextTypes.DEFAULT_TYPE):
    resetFlags(update.effective_chat.id)
    await mostrarMenuPrincipal("",update,context)

async def naoDesejaSenha(update: Update, context: ContextTypes.DEFAULT_TYPE):
    curso_id = sha256((str(update.effective_chat.id) + "curso" + temp_dados_curso[update.effective_chat.id]['nome']).encode('utf-8')).hexdigest()[:15]
    call_database_and_execute("INSERT INTO cursos (nome,descricao,hash_senha,dono_id,id) VALUES (?,?,?,?,?)",[
        temp_dados_curso[update.effective_chat.id]["nome"],
        temp_dados_curso[update.effective_chat.id]["descricao"],
        "",
        update.effective_chat.id,
        curso_id
    ])
    resetFlags(update.effective_chat.id)
    await menuCurso(curso_id,update,context)

async def handleGenericCallback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    print('calling handle generic callback!')
    query = update.callback_query.data
    if len(query.split(' ')) > 1:
        if query.split()[0] == "ver_curso_especifico":
            await menuCurso(query.split()[1],update,context)
            return
        if query.split()[0] == "receber_id_curso":
            await context.bot.send_message(chat_id=update.effective_chat.id,text=query.split()[1])


if __name__ == '__main__':

    if not os.path.exists("database.db"):
        call_database_and_execute("""
        CREATE TABLE IF NOT EXISTS users (
            user_id INTEGER PRIMARY KEY
        )""")

        call_database_and_execute("""
        CREATE TABLE IF NOT EXISTS cursos (
            nome TEXT,
            descricao TEXT,
            dono_id INTEGER,
            hash_senha TEXT,
            id TEXT
        )""")

        call_database_and_execute("""
        CREATE TABLE IF NOT EXISTS aulas_por_curso (
            aula_id TEXT,
            curso_id TEXT,
            descricao TEXT,
            arquivos TEXT
        )""")

        call_database_and_execute("""
        CREATE TABLE IF NOT EXISTS alunos_por_curso (
            aluno_id INTEGER,
            curso_id TEXT,
            aulas_completas TEXT
        )""")

    application = ApplicationBuilder().token('5507439323:AAGiiQ0_vnqIilIRBPRBtGnS54eje4D5xVE').build()
    
    
    

    start_handler = CommandHandler('start', start)

    application.add_handler(start_handler)
    application.add_handler(MessageHandler(callback=messageHandler,filters=filters.TEXT))
    application.add_handler(CallbackQueryHandler(callback=criarCurso,pattern='criar_curso'))
    application.add_handler(CallbackQueryHandler(callback=naoDesejaCriarCurso,pattern='nao_deseja_criar_curso'))
    application.add_handler(CallbackQueryHandler(callback=voltarAoMenu,pattern='voltar_ao_menu'))
    application.add_handler(CallbackQueryHandler(callback=naoDesejaSenha,pattern='nao_deseja_colocar_senha_em_curso'))
    application.add_handler(CallbackQueryHandler(callback=verCursos,pattern='ver_cursos'))
    application.add_handler(CallbackQueryHandler(callback=handleGenericCallback))
    
    application.run_polling()