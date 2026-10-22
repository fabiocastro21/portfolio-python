import os
import sys
import sqlite3


def obter_caminho_banco():
    if getattr(sys, "frozen", False):
        pasta_programa = os.path.dirname(sys.executable)
    else:
        pasta_programa = os.path.dirname(os.path.abspath(__file__))
    return os.path.join(pasta_programa, "biblioteca.db")


def conectar():
    conexao = sqlite3.connect(obter_caminho_banco())
    conexao.execute("PRAGMA foreign_keys = ON")
    
    cursor = conexao.cursor()
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS status (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            nome TEXT NOT NULL
        )
    """)
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS categorias (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            nome TEXT NOT NULL UNIQUE
        )
    """)
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS livros (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            titulo TEXT NOT NULL,
            status_id INTEGER,
            observacoes TEXT,
            FOREIGN KEY (status_id) REFERENCES status (id)
        )
    """)
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS livro_categoria (
            livro_id INTEGER,
            categoria_id INTEGER,
            PRIMARY KEY (livro_id, categoria_id),
            FOREIGN KEY (livro_id) REFERENCES livros (id),
            FOREIGN KEY (categoria_id) REFERENCES categorias (id)
        )
    """)
    
    cursor.execute("SELECT COUNT(*) FROM status")
    if cursor.fetchone()[0] == 0:
        cursor.executemany(
            "INSERT INTO status (id, nome) VALUES (?, ?)",
            [
                (1, "nao lido"),
                (2, "lendo"),
                (3, "lido"),
                (4, "Livro de consulta")
            ]
        )
    
    conexao.commit()
    return conexao


def listar_livros():
    conexao = conectar()
    cursor = conexao.cursor()
    cursor.execute("""
        SELECT livros.id, livros.titulo, status.nome, GROUP_CONCAT(categorias.nome, ', ')
        FROM livros
        LEFT JOIN status ON livros.status_id = status.id
        LEFT JOIN livro_categoria ON livros.id = livro_categoria.livro_id
        LEFT JOIN categorias ON livro_categoria.categoria_id = categorias.id
        GROUP BY livros.id, livros.titulo, status.nome
        ORDER BY livros.id
    """)
    livros = cursor.fetchall()
    conexao.close()
    return livros


def buscar_livros_filtros(titulo="", status_id=0, categoria_id=0):
    conexao = conectar()
    cursor = conexao.cursor()
    
    query = """
        SELECT livros.id, livros.titulo, status.nome, GROUP_CONCAT(categorias2.nome, ', ')
        FROM livros
        LEFT JOIN status ON livros.status_id = status.id
        LEFT JOIN livro_categoria ON livros.id = livro_categoria.livro_id
        LEFT JOIN categorias ON livro_categoria.categoria_id = categorias.id
        LEFT JOIN livro_categoria AS lc2 ON livros.id = lc2.livro_id
        LEFT JOIN categorias AS categorias2 ON lc2.categoria_id = categorias2.id
        WHERE 1=1
    """
    params = []

    if titulo:
        query += " AND livros.titulo LIKE ?"
        params.append(f"%{titulo}%")
    
    if status_id > 0:
        query += " AND livros.status_id = ?"
        params.append(status_id)

    if categoria_id > 0:
        query += " AND categorias.id = ?"
        params.append(categoria_id)

    query += """
        GROUP BY livros.id, livros.titulo, status.nome
        ORDER BY livros.titulo
    """

    cursor.execute(query, params)
    livros = cursor.fetchall()
    conexao.close()
    return livros


def obter_detalhes_livro(livro_id):
    conexao = conectar()
    cursor = conexao.cursor()
    
    cursor.execute("""
        SELECT livros.id, livros.titulo, status.nome, livros.observacoes, livros.status_id
        FROM livros
        LEFT JOIN status ON livros.status_id = status.id
        WHERE livros.id = ?
    """, (livro_id,))
    livro = cursor.fetchone()
    
    cursor.execute("""
        SELECT categorias.id, categorias.nome
        FROM categorias
        JOIN livro_categoria ON categorias.id = livro_categoria.categoria_id
        WHERE livro_categoria.livro_id = ?
        ORDER BY categorias.nome
    """, (livro_id,))
    categorias = cursor.fetchall()
    
    conexao.close()
    return livro, categorias


def obter_categorias():
    conexao = conectar()
    cursor = conexao.cursor()
    cursor.execute("SELECT id, nome FROM categorias ORDER BY nome")
    categorias = cursor.fetchall()
    conexao.close()
    return categorias


def obter_status():
    conexao = conectar()
    cursor = conexao.cursor()
    cursor.execute("SELECT id, nome FROM status ORDER BY id")
    status = cursor.fetchall()
    conexao.close()
    return status


def salvar_livro(titulo, status_id, observacoes, ids_categorias):
    conexao = conectar()
    cursor = conexao.cursor()
    cursor.execute("""
        INSERT INTO livros (titulo, status_id, observacoes)
        VALUES (?, ?, ?)
    """, (titulo, status_id, observacoes))
    livro_id = cursor.lastrowid

    for id_cat in ids_categorias:
        cursor.execute("""
            INSERT INTO livro_categoria (livro_id, categoria_id)
            VALUES (?, ?)
        """, (livro_id, id_cat))

    conexao.commit()
    conexao.close()


def atualizar_livro_bd(livro_id, titulo, status_id, observacoes, ids_categorias):
    conexao = conectar()
    cursor = conexao.cursor()
    
    cursor.execute("""
        UPDATE livros
        SET titulo = ?, status_id = ?, observacoes = ?
        WHERE id = ?
    """, (titulo, status_id, observacoes, livro_id))
    
    cursor.execute("DELETE FROM livro_categoria WHERE livro_id = ?", (livro_id,))
    
    for id_cat in ids_categorias:
        cursor.execute("""
            INSERT INTO livro_categoria (livro_id, categoria_id)
            VALUES (?, ?)
        """, (livro_id, id_cat))
        
    conexao.commit()
    conexao.close()


def deletar_livro_bd(livro_id):
    conexao = conectar()
    cursor = conexao.cursor()
    cursor.execute("DELETE FROM livro_categoria WHERE livro_id = ?", (livro_id,))
    cursor.execute("DELETE FROM livros WHERE id = ?", (livro_id,))
    conexao.commit()
    conexao.close()


def adicionar_categoria_bd(nome):
    conexao = conectar()
    cursor = conexao.cursor()
    cursor.execute("SELECT id FROM categorias WHERE nome = ?", (nome,))
    if cursor.fetchone():
        conexao.close()
        return False

    cursor.execute("INSERT INTO categorias (nome) VALUES (?)", (nome,))
    conexao.commit()
    conexao.close()
    return True


def obter_estatisticas_completas():
    conexao = conectar()
    cursor = conexao.cursor()
    
    cursor.execute("SELECT COUNT(*) FROM livros")
    tot_livros = cursor.fetchone()[0]
    
    cursor.execute("SELECT COUNT(*) FROM categorias")
    tot_categorias = cursor.fetchone()[0]

    cursor.execute("SELECT COUNT(*) FROM livro_categoria")
    tot_relacoes = cursor.fetchone()[0]

    cursor.execute("""
        SELECT status.nome, COUNT(livros.id)
        FROM status
        LEFT JOIN livros ON livros.status_id = status.id
        GROUP BY status.id, status.nome
        ORDER BY status.id
    """)
    por_status = cursor.fetchall()

    cursor.execute("""
        SELECT categorias.nome, COUNT(livro_categoria.livro_id)
        FROM categorias
        LEFT JOIN livro_categoria ON categorias.id = livro_categoria.categoria_id
        GROUP BY categorias.id, categorias.nome
        ORDER BY COUNT(livro_categoria.livro_id) DESC, categorias.nome
    """)
    por_categoria = cursor.fetchall()

    conexao.close()
    return tot_livros, tot_categorias, tot_relacoes, por_status, por_categoria