import multiprocessing
import os
import subprocess

from geral import call_database_and_execute


cursos_process = multiprocessing.Process(
    target=subprocess.run,
    kwargs={
        'args': f'python3 bot_cursos.py',
        'shell': True

    })


alunos_process= multiprocessing.Process(
    target=subprocess.run,
    kwargs={
        'args': f'python3 bot_alunos.py',
        'shell': True
    })


if __name__ == "__main__":

    if not os.path.exists("database.db"):
        #criando o banco de dados caso não exista ainda
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
            titulo TEXT,
            descricao TEXT,
            links TEXT
        )""")

        call_database_and_execute("""
        CREATE TABLE IF NOT EXISTS alunos_por_curso (
            aluno_id INTEGER,
            curso_id TEXT,
            aulas_completas TEXT
        )""")

    cursos_process.start()
    alunos_process.start()