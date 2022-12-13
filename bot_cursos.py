import logging
from telegram import Update,InlineKeyboardButton
from telegram.ext import ApplicationBuilder,MessageHandler, ContextTypes, CommandHandler,CallbackQueryHandler
import telegram.ext.filters as filters
import telegram
from telegram.constants import ParseMode
import sqlite3 as sql
import os
from typing import List
from copy import deepcopy
import csv
import time

from geral import call_database_and_execute, hash_string



# definindo como o log vai ser salvo
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)

# dicionario para guardar o id da ultima mensagem mandada p/ cada usuário
# serve para evitar mandarmos muitas mensagens
last_messages = {}

# flags por usuário para controlar em qual estágio da conversa ele está
flags_per_user = {}

# dicionario para guardar os dados temporários quando estiver criando um curso novo
temp_dados_curso = {}



flags = {
    "criando_curso":False,
    "editando_curso":False,
        "mandando_nome_curso":False,
        "mandando_descricao_curso":False,
        "mandando_senha_curso":False,
        #etc
    "editando_aulas":False,
        "mandando_arquivo":False
}

def reset_temp_curso(user_id):
    temp_dados_curso[user_id] = {"nome":"","descricao":"","senha":"","id":""}

def make_sure_flags_are_init(user_id):
    """função auxiliar para garantir que não vamos acessar um usuário não existente"""
    if user_id not in flags_per_user:
        flags_per_user[user_id] = deepcopy(flags)



def reset_flags(user_id):
    """função auxiliar para resetar as flags"""
    flags_per_user[user_id] = deepcopy(flags)
    reset_temp_curso(user_id)

    
# função auxiliar para evitar mudar uma mensagem muito atrás
def reset_last_message(user_id):
    if user_id in last_messages:
        del last_messages[user_id]

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


async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """função chamada quando uma conversa nova é iniciada ou ao mandar um /start"""
    
    data = call_database_and_execute("SELECT * FROM users WHERE user_id = ?",(update.effective_user.id,))
    reset_flags(update.effective_chat.id)
    reset_last_message(update.effective_chat.id)
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

        await mostrar_menu_principal(message,update,context)






async def mostrar_menu_principal(message: str,update: Update,context: ContextTypes.DEFAULT_TYPE):
    """
    função para mostrar o menu principal (pode ser chamada em qualquer outra resposta)
    """
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



async def message_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """
    função para lidar com mensagens enviadas pelo usuário (respostas ao bot, por exemplo)
    """
    print('calling message handler!')
    make_sure_flags_are_init(update.effective_chat.id)

    if flags_per_user[update.effective_chat.id]['criando_curso']:
        if flags_per_user[update.effective_chat.id]["mandando_nome_curso"]:
            temp_dados_curso[update.effective_chat.id]['nome'] = update.effective_message.text
            await send_message_on_new_block(update,context,text="Ok! Agora me diga uma breve descrição do seu curso",
                buttons=[
                    [
                        InlineKeyboardButton("voltar ao menu",callback_data="voltar_ao_menu")
                    ]
                ]
            )
            flags_per_user[update.effective_chat.id]["mandando_nome_curso"] = False
            flags_per_user[update.effective_chat.id]["mandando_descricao_curso"] = True
            return
        if flags_per_user[update.effective_chat.id]["mandando_descricao_curso"]:
            temp_dados_curso[update.effective_chat.id]['descricao'] = update.effective_message.text
            flags_per_user[update.effective_chat.id]["mandando_descricao_curso"] = False
            flags_per_user[update.effective_chat.id]["mandando_senha_curso"] = True
            await send_message_on_new_block(update,context,text="Ok! Agora me diga a senha para os alunos entrarem no seu curso",
                buttons=[
                    [
                        InlineKeyboardButton("não desejo colocar",callback_data="nao_deseja_colocar_senha_em_curso")
                    ],
                    [
                        InlineKeyboardButton("voltar ao menu",callback_data="voltar_ao_menu")
                    ]
                ]
            )
            return
        if flags_per_user[update.effective_chat.id]["mandando_senha_curso"]:
            temp_dados_curso[update.effective_chat.id]['senha'] = update.effective_message.text
            curso_id = hash_string(str(update.effective_chat.id) + "curso" + temp_dados_curso[update.effective_chat.id]['nome'])
            call_database_and_execute("INSERT INTO cursos (nome,descricao,hash_senha,dono_id,id) VALUES (?,?,?,?,?)",[
                temp_dados_curso[update.effective_chat.id]["nome"],
                temp_dados_curso[update.effective_chat.id]["descricao"],
                hash_string(temp_dados_curso[update.effective_chat.id]["senha"]),
                update.effective_chat.id,
                curso_id
            ])
            reset_flags(update.effective_chat.id)
            reset_last_message(update.effective_chat.id)
            await menu_curso(curso_id,update,context)
            return
    if flags_per_user[update.effective_chat.id]['editando_curso']:
        if flags_per_user[update.effective_chat.id]["mandando_nome_curso"]:
            id = temp_dados_curso[update.effective_chat.id]['id']
            call_database_and_execute("UPDATE cursos SET nome = ? WHERE id = ?",[update.effective_message.text,id])
            reset_flags(user_id=update.effective_chat.id)
            await send_message_on_new_block(update,context,text="Nome atualizado!")
            await menu_curso(id,update,context)
            return

        if flags_per_user[update.effective_chat.id]["mandando_descricao_curso"]:
            id = temp_dados_curso[update.effective_chat.id]['id']
            call_database_and_execute("UPDATE cursos SET descricao = ? WHERE id = ?",[update.effective_message.text,id])
            reset_flags(user_id=update.effective_chat.id)
            await send_message_on_new_block(update,context,text="Descrição atualizada!")
            await menu_curso(id,update,context)
            return
        
        if flags_per_user[update.effective_chat.id]['mandando_senha_curso']:
            id = temp_dados_curso[update.effective_chat.id]['id']
            call_database_and_execute("UPDATE cursos SET hash_senha = ? WHERE id = ?",[hash_string(update.effective_message.text),id])
            reset_flags(user_id=update.effective_chat.id)
            await send_message_on_new_block(update,context,text="Senha atualizada!")
            await menu_curso(id,update,context)


    


async def menu_curso(id_curso: str,update: Update,context: ContextTypes.DEFAULT_TYPE):
    """
    função para mostrar o menu de um curso específico
    """
    dados_curso = call_database_and_execute("SELECT * FROM cursos WHERE id = ?",[id_curso])
    print(dados_curso)
    buttons = [
            [
                InlineKeyboardButton(text="ver id do curso",callback_data=f"receber_id_curso {id_curso}")
            ],
            [
                InlineKeyboardButton(text="editar nome",callback_data=f"editar_nome_curso {id_curso}")
            ],
            [
                InlineKeyboardButton(text="editar senha",callback_data=f"editar_senha {id_curso}")
            ],
            [
                InlineKeyboardButton(text="editar descrição",callback_data=f"editar_descricao_curso {id_curso}")
            ],
            [
                InlineKeyboardButton(text="ver aulas",callback_data=f"editar_aulas {id_curso}")
            ],
            [
                InlineKeyboardButton(text="voltar ao menu",callback_data="voltar_ao_menu")
            ],
        ]
    text = f"O que você gostaria de editar?\n\nCurso atual: {dados_curso[0]['nome']}\n\nPrecisa de senha? {dados_curso[0]['hash_senha'] != ''}\n\nDescrição do curso: {dados_curso[0]['descricao']}"
    await send_message_or_edit_last(update,context,text=text,buttons=buttons)


async def ver_cursos(update: Update,context: ContextTypes.DEFAULT_TYPE):
    """
    função para mostrar todos os cursos já criados
    """
    data = call_database_and_execute("SELECT nome,id FROM cursos WHERE dono_id = ?",[update.effective_chat.id])
    print(list(map(lambda i: len(f'ver_curso_especifico {i["id"]}'.encode('utf-8')),data)))
    buttons = [[InlineKeyboardButton(text=i['nome'],callback_data=f'ver_curso_especifico {i["id"]}')] for i in data]
    buttons.append([InlineKeyboardButton(text="voltar ao menu",callback_data='voltar_ao_menu')])
    await send_message_or_edit_last(update,context,text="Qual curso você deseja editar?",buttons=buttons)
        

async def criar_curso(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """
    função para iniciar o diálogo de criação de curso
    """
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
        temp_dados_curso[update.effective_chat.id] = {"nome":"","descricao":"","senha":"","id":""}


async def nao_deseja_criar_curso(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """
    função para quando o usuário não deseja criar uma conta ou interagir com o bot agora
    """
    if update.effective_chat.id in last_messages:
        await context.bot.edit_message_text(chat_id=update.effective_chat.id,message_id=last_messages[update.effective_chat.id],text="Tudo certo!\n\nQuando quiser utilizar meus serviços digite /start nesse chat e eu virei te ajudar!\n\nTenha um bom dia :D")
    else:
        await context.bot.send_message(chat_id=update.effective_chat.id,text="Tudo certo!\n\nQuando quiser utilizar meus serviços digite /start nesse chat e eu virei te ajudar!\n\nTenha um bom dia :D")

async def voltar_ao_menu(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """
    função para voltar ao menu principal (usada como callback dos botões inlines com o callback_data = "voltar_ao_menu")
    """
    reset_flags(update.effective_chat.id)
    await mostrar_menu_principal("",update,context)

async def nao_deseja_senha(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """
    função quando o usuário deseja criar um curso sem senha
    """
    curso_id = hash_string(str(update.effective_chat.id) + "curso" + temp_dados_curso[update.effective_chat.id]['nome'])
    call_database_and_execute("INSERT INTO cursos (nome,descricao,hash_senha,dono_id,id) VALUES (?,?,?,?,?)",[
        temp_dados_curso[update.effective_chat.id]["nome"],
        temp_dados_curso[update.effective_chat.id]["descricao"],
        "",
        update.effective_chat.id,
        curso_id
    ])
    reset_flags(update.effective_chat.id)
    await menu_curso(curso_id,update,context)

async def ver_aulas(id_curso: str,update: Update, context: ContextTypes.DEFAULT_TYPE):
    reset_flags(update.effective_chat.id)
    """
    função para mostrar as aulas cadastradas ou uma mensagem caso nenhum esteja cadastrada
    """
    dados = call_database_and_execute("SELECT * FROM aulas_por_curso WHERE curso_id = ?",[id_curso])
    if len(dados) == 0:
        await send_message_or_edit_last(update,context,text="""Vejo que você não cadastrou nenhuma aula nesse curso ainda, gostaria de cadastrar novas aulas?""",buttons=[
            [
                InlineKeyboardButton(text="sim, usando Excel",callback_data=f"enviar_aulas_excel {id_curso}")
            ],
            [
                InlineKeyboardButton(text="sim, uma por uma",callback_data=f"enviar_aulas {id_curso}")
            ],
            [
                InlineKeyboardButton(text="voltar",callback_data=f"ver_curso_especifico {id_curso}")
            ]
        ])
    else:
        buttons = [[InlineKeyboardButton(f'{i + 1} {data["titulo"]}',callback_data=f"ver_aula {data['aula_id']}")] for i,data in enumerate(dados)]

        buttons.append([InlineKeyboardButton("voltar",callback_data=f"ver_curso_especifico {id_curso}")])

        await send_message_or_edit_last(update,context,text="Qual aula você gostaria de editar?",buttons=buttons)
        return

async def cadastrar_aulas_excel(id_curso: str,update: Update, context: ContextTypes.DEFAULT_TYPE):
    """
    função para direcionar o usuário sobre como formatar o arquivo excel e processar os dados
    """
    await send_message_or_edit_last(update,context,text="""Ok! Para enviar as suas aulas no arquivo excel, por favor crie as colunas

TITULO | DESCRICAO | LINKS
    
em letra maiúscula exatamente como está escrito acima em um arquivo ".csv". Ai só mandar aqui que eu vou adicionar lá!""",buttons=[
    [
        InlineKeyboardButton(text="voltar",callback_data=f'ver_aulas {id_curso}')
    ]
])  
    reset_flags(update.effective_chat.id)
    flags_per_user[update.effective_chat.id]['editando_aulas'] = True
    flags_per_user[update.effective_chat.id]['mandando_arquivo'] = True
    temp_dados_curso[update.effective_chat.id]['id'] = id_curso
    return

async def handle_generic_csv_file_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not os.path.exists("downloads"):
        os.mkdir('downloads')
    if flags_per_user[update.effective_chat.id]['editando_aulas']:
        if flags_per_user[update.effective_chat.id]['mandando_arquivo']:
            await (await context.bot.get_file(update.message.document)).download(f"downloads/{update.message.document.file_unique_id}.csv")

            with open(f"downloads/{update.message.document.file_unique_id}.csv",'r') as f:
                try:
                    file = csv.DictReader(f)
                    rows = []
                    for row in file:
                        if "TITULO" not in row.keys():
                            await send_message_on_new_block(update,context,text=f"O seu arquivo está com o campo 'TITULO' inexistente. Por favor corrija e tente novamente")
                            return
                        if "DESCRICAO" not in row.keys():
                            await send_message_on_new_block(update,context,text=f"O seu arquivo está com o campo 'DESCRICAO' inexistente. Por favor corrija e tente novamente")
                            return
                        if "LINKS" not in row.keys():
                            await send_message_on_new_block(update,context,text=f"O seu arquivo está com o campo 'LINKS' inexistente. Por favor corrija e tente novamente")
                            return
                        rows.append(row)
                    
                    for row in rows:
                        
                        call_database_and_execute("INSERT INTO aulas_por_curso (aula_id,curso_id,titulo,descricao,links) VALUES (?,?,?,?,?)",[
                            hash_string(f'{update.effective_chat.id}_{time.time()}'),
                            temp_dados_curso[update.effective_chat.id]['id'],
                            row["TITULO"],
                            row["DESCRICAO"],
                            row['LINKS']
                        ])
                    print('finished handling file!')
                    os.remove(f"downloads/{update.message.document.file_unique_id}.csv")
                    await ver_aulas(temp_dados_curso[update.effective_chat.id]['id'],update,context)
                except Exception as e:
                    await send_message_on_new_block(update,context,text=f"Um erro ocorreu enquanto eu lia esse arquivo. Por favor envie esse log para os donos do bot!\n\nError: {e}")
                    os.remove(f"downloads/{update.message.document.file_unique_id}.csv")
                    return

    

async def handle_generic_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """
    função para lidar com callbacks genéricos ou que possuem algum dado extra (como id do curso por exemplo)
    """

    make_sure_flags_are_init(update.effective_chat.id)
    reset_temp_curso(update.effective_chat.id)
    print('calling handle generic callback!')
    query = update.callback_query.data
    if len(query.split(' ')) > 1:
        descricao_ordem, dados = query.split()
        if descricao_ordem == "ver_curso_especifico":
            print("calling curso!")
            await menu_curso(query.split()[1],update,context)
            return
        if descricao_ordem == "receber_id_curso":
            await context.bot.send_message(chat_id=update.effective_chat.id,text=query.split()[1])
            return

        if descricao_ordem == "editar_nome_curso":
            await send_message_or_edit_last(update,context,text="Ok! Qual nome você deseja associar a esse curso?",
                buttons=[
                    [
                        InlineKeyboardButton(text="voltar",callback_data=f"ver_curso_especifico {dados}")
                    ]
                ]
            )
            reset_flags(update.effective_chat.id)
            temp_dados_curso[update.effective_chat.id]['id'] = dados
            flags_per_user[update.effective_chat.id]['editando_curso'] = True
            flags_per_user[update.effective_chat.id]['mandando_nome_curso'] = True
            return
        
        if descricao_ordem == "editar_descricao_curso":
            await send_message_or_edit_last(update,context,text="Ok! Me diga qual descrição você gostaria de colocar nesse curso...",
                buttons=[
                    [
                        InlineKeyboardButton(text="voltar",callback_data=f"ver_curso_especifico {dados}")
                    ]
                ]
            )
            reset_flags(update.effective_chat.id)
            temp_dados_curso[update.effective_chat.id]['id'] = dados
            flags_per_user[update.effective_chat.id]['editando_curso'] = True
            flags_per_user[update.effective_chat.id]['mandando_descricao_curso'] = True
            return
        if descricao_ordem == 'editar_senha':
            buttons = [
                    [
                        InlineKeyboardButton(text="voltar",callback_data=f"ver_curso_especifico {dados}")
                    ]
                ]
            dados_curso = call_database_and_execute("SELECT hash_senha FROM cursos WHERE id = ?",[dados])
            if dados_curso[0]["hash_senha"] != "":
                buttons.append([
                        InlineKeyboardButton(text="quero remover a senha",callback_data=f"remover_senha {dados}")
                    ])
                buttons.reverse()
            await send_message_or_edit_last(update,context,text="Ok! Me diga a nova senha para entrar nesse curso (os usuários antigos continuarão cadastrados)...",
                buttons=buttons
            )
            reset_flags(update.effective_chat.id)
            temp_dados_curso[update.effective_chat.id]['id'] = dados
            flags_per_user[update.effective_chat.id]['editando_curso'] = True
            flags_per_user[update.effective_chat.id]['mandando_senha_curso'] = True
            return
        if descricao_ordem == 'remover_senha':
            call_database_and_execute("UPDATE cursos SET hash_senha = ? WHERE id = ?",["",dados])
            reset_flags(update.effective_chat.id)
            await send_message_on_new_block(update,context,"Senha atualizada!")
            await menu_curso(dados,update,context)
            return

        if descricao_ordem == "editar_aulas":
            await ver_aulas(dados,update,context)
            return

        if descricao_ordem == "enviar_aulas_excel":
            await cadastrar_aulas_excel(dados,update,context)
            return 

        if descricao_ordem == "enviar_aulas":
            #TODO
            pass

            


if __name__ == '__main__':

    application = ApplicationBuilder().token('5507439323:AAGiiQ0_vnqIilIRBPRBtGnS54eje4D5xVE').build()
    
    
    

    start_handler = CommandHandler('start', start)

    application.add_handler(start_handler)
    application.add_handler(MessageHandler(callback=handle_generic_csv_file_callback,filters=filters.Document.FileExtension("csv")))
    application.add_handler(MessageHandler(callback=message_handler,filters=filters.TEXT))
    application.add_handler(CallbackQueryHandler(callback=criar_curso,pattern='criar_curso'))
    application.add_handler(CallbackQueryHandler(callback=nao_deseja_criar_curso,pattern='nao_deseja_criar_curso'))
    application.add_handler(CallbackQueryHandler(callback=voltar_ao_menu,pattern='voltar_ao_menu'))
    application.add_handler(CallbackQueryHandler(callback=nao_deseja_senha,pattern='nao_deseja_colocar_senha_em_curso'))
    application.add_handler(CallbackQueryHandler(callback=ver_cursos,pattern='ver_cursos'))
    application.add_handler(CallbackQueryHandler(callback=handle_generic_callback))
    
    application.run_polling()