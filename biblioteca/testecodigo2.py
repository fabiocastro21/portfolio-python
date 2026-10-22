import os
import sys
import sqlite3


# ============================================================
# CAMINHO DO BANCO DE DADOS
# ============================================================

def obter_caminho_banco():
    """
    Retorna o caminho do banco biblioteca.db.

    Quando executado pelo Python:
        usa a pasta deste arquivo .py.

    Quando compilado para .exe com PyInstaller:
        usa a pasta onde está o .exe.
    """

    if getattr(sys, "frozen", False):
        # Executando como .exe
        pasta_programa = os.path.dirname(sys.executable)
    else:
        # Executando como .py
        pasta_programa = os.path.dirname(os.path.abspath(__file__))

    return os.path.join(pasta_programa, "biblioteca.db")


# ============================================================
# CONEXÃO COM O BANCO
# ============================================================

def conectar():
    caminho = obter_caminho_banco()

    conexao = sqlite3.connect(caminho)

    # Ativa chaves estrangeiras
    conexao.execute("PRAGMA foreign_keys = ON")

    return conexao


# ============================================================
# LISTAR LIVROS
# ============================================================

def listar_livros():

    conexao = conectar()
    cursor = conexao.cursor()

    cursor.execute("""
        SELECT
            livros.id,
            livros.titulo,
            status.nome,
            GROUP_CONCAT(categorias.nome, ', ')
        FROM livros

        LEFT JOIN status
            ON livros.status_id = status.id

        LEFT JOIN livro_categoria
            ON livros.id = livro_categoria.livro_id

        LEFT JOIN categorias
            ON livro_categoria.categoria_id = categorias.id

        GROUP BY
            livros.id,
            livros.titulo,
            status.nome

        ORDER BY livros.id
    """)

    livros = cursor.fetchall()

    conexao.close()

    return livros


# ============================================================
# BUSCAR LIVRO POR ID
# ============================================================

def buscar_livro(id):

    conexao = conectar()
    cursor = conexao.cursor()

    cursor.execute("""
        SELECT
            livros.id,
            livros.titulo,
            status.nome,
            livros.observacoes
        FROM livros

        LEFT JOIN status
            ON livros.status_id = status.id

        WHERE livros.id = ?
    """, (id,))

    livro = cursor.fetchone()

    conexao.close()

    return livro


# ============================================================
# VISUALIZAR LIVRO
# ============================================================

def visualizar_livro():

    livros = listar_livros()

    if len(livros) == 0:
        print("\nNão há livros cadastrados!")
        return

    print("\n|========== LIVROS ==========|")

    for livro in livros:
        print(
            f"{livro[0]} - "
            f"{livro[1]} - "
            f"{livro[2]} - "
            f"{livro[3]}"
        )

    try:
        escolha = int(
            input("\nDigite o ID do livro que deseja ler: ")
        )
    except ValueError:
        print("\nID inválido!")
        return

    livro = buscar_livro(escolha)

    if livro is None:
        print("\nLivro não encontrado!")
        return

    conexao = conectar()
    cursor = conexao.cursor()

    cursor.execute("""
        SELECT categorias.nome

        FROM categorias

        JOIN livro_categoria
            ON categorias.id = livro_categoria.categoria_id

        WHERE livro_categoria.livro_id = ?

        ORDER BY categorias.nome
    """, (escolha,))

    categorias = cursor.fetchall()

    conexao.close()

    print("\n|========== LIVRO ==========|")

    print(f"\nID: {livro[0]}")
    print(f"Título: {livro[1]}")
    print(f"Status: {livro[2]}")

    print("\nCategorias:")

    if len(categorias) == 0:
        print("Nenhuma categoria cadastrada.")
    else:
        for categoria in categorias:
            print(f"- {categoria[0]}")

    print(f"\nObservações: {livro[3]}")

    print("\n|============================|")


# ============================================================
# ADICIONAR LIVRO
# ============================================================

def adicionar_livro():

    titulo = input("Título do livro: ").strip()

    if titulo == "":
        print("\nO título não pode ficar vazio!")
        return

    observacoes = input("Observações: ")

    print("\nStatus:")
    print("1 - não lido")
    print("2 - lendo")
    print("3 - lido")
    print("4 - Livro de consulta")

    try:
        escolha_status = int(
            input("Escolha o status: ")
        )
    except ValueError:
        print("\nStatus inválido!")
        return

    if escolha_status < 1 or escolha_status > 4:
        print("\nStatus inválido!")
        return

    conexao = conectar()
    cursor = conexao.cursor()

    cursor.execute("""
        SELECT id, nome
        FROM categorias
        ORDER BY nome
    """)

    categorias = cursor.fetchall()

    if len(categorias) == 0:
        print("\nNão existem categorias cadastradas!")
        conexao.close()
        return

    print("\nCategorias disponíveis:")

    for categoria in categorias:
        print(f"{categoria[0]} - {categoria[1]}")

    escolha_categorias = input(
        "\nDigite os IDs das categorias separados por vírgula: "
    )

    try:

        ids_categorias = [
            int(id_categoria.strip())
            for id_categoria in escolha_categorias.split(",")
            if id_categoria.strip() != ""
        ]

    except ValueError:

        print("\nCategoria inválida!")
        conexao.close()
        return

    if len(ids_categorias) == 0:
        print("\nVocê precisa informar pelo menos uma categoria!")
        conexao.close()
        return

    ids_validos = [categoria[0] for categoria in categorias]

    for id_categoria in ids_categorias:

        if id_categoria not in ids_validos:

            print(
                f"\nA categoria {id_categoria} não existe!"
            )

            conexao.close()
            return

    cursor.execute("""
        INSERT INTO livros (
            titulo,
            status_id,
            observacoes
        )

        VALUES (?, ?, ?)
    """, (
        titulo,
        escolha_status,
        observacoes
    ))

    livro_id = cursor.lastrowid

    for id_categoria in ids_categorias:

        cursor.execute("""
            INSERT INTO livro_categoria (
                livro_id,
                categoria_id
            )

            VALUES (?, ?)
        """, (
            livro_id,
            id_categoria
        ))

    conexao.commit()
    conexao.close()

    print("\nLivro cadastrado!")


# ============================================================
# DELETAR LIVRO
# ============================================================

def deletar_livro():

    livros = listar_livros()

    if len(livros) == 0:
        print("\nNão há livros cadastrados!")
        return

    print("\n|========== LIVROS ==========|")

    for livro in livros:
        print(
            f"{livro[0]} - "
            f"{livro[1]} - "
            f"{livro[2]}"
        )

    try:
        escolha = int(
            input(
                "\nDigite o ID do livro que deseja deletar: "
            )
        )
    except ValueError:
        print("\nID inválido!")
        return

    livro = buscar_livro(escolha)

    if livro is None:
        print("\nLivro não encontrado!")
        return

    print(f"\nLivro selecionado: {livro[1]}")

    confirmacao = input(
        "Tem certeza que deseja deletar? [s/n]: "
    )

    if confirmacao.lower() != "s":

        print("\nOperação cancelada.")
        return

    conexao = conectar()
    cursor = conexao.cursor()

    # Primeiro remove as relações
    cursor.execute("""
        DELETE FROM livro_categoria
        WHERE livro_id = ?
    """, (escolha,))

    # Depois remove o livro
    cursor.execute("""
        DELETE FROM livros
        WHERE id = ?
    """, (escolha,))

    conexao.commit()
    conexao.close()

    print("\nLivro deletado!")


# ============================================================
# ATUALIZAR LIVRO
# ============================================================

def atualizar_livro():

    livros = listar_livros()

    if len(livros) == 0:
        print("\nNão há livros cadastrados!")
        return

    print("\n|========== LIVROS ==========|")

    for livro in livros:
        print(
            f"{livro[0]} - "
            f"{livro[1]} - "
            f"{livro[2]} - "
            f"{livro[3]}"
        )

    try:
        escolha = int(
            input(
                "\nDigite o ID do livro que deseja alterar: "
            )
        )
    except ValueError:
        print("\nID inválido!")
        return

    livro = buscar_livro(escolha)

    if livro is None:
        print("\nLivro não encontrado!")
        return

    print("\n|========== LIVRO ==========|")

    print(f"ID: {livro[0]}")
    print(f"Título: {livro[1]}")
    print(f"Status atual: {livro[2]}")
    print(f"Observações atuais: {livro[3]}")

    conexao = conectar()
    cursor = conexao.cursor()

    cursor.execute("""
        SELECT
            categorias.id,
            categorias.nome

        FROM categorias

        JOIN livro_categoria
            ON categorias.id = livro_categoria.categoria_id

        WHERE livro_categoria.livro_id = ?

        ORDER BY categorias.nome
    """, (escolha,))

    categorias_atuais = cursor.fetchall()

    print("\nCategorias atuais:")

    if len(categorias_atuais) == 0:
        print("Nenhuma categoria.")
    else:
        for categoria in categorias_atuais:
            print(f"- {categoria[1]}")

    print("\nStatus disponíveis:")
    print("1 - não lido")
    print("2 - lendo")
    print("3 - lido")
    print("4 - Livro de consulta")

    try:
        novo_status = int(
            input("\nEscolha o novo status: ")
        )
    except ValueError:
        print("\nStatus inválido!")
        conexao.close()
        return

    if novo_status < 1 or novo_status > 4:
        print("\nStatus inválido!")
        conexao.close()
        return

    nova_observacao = input(
        "\nDigite as novas observações: "
    )

    cursor.execute("""
        SELECT id, nome

        FROM categorias

        ORDER BY nome
    """)

    categorias = cursor.fetchall()

    print("\nCategorias disponíveis:")

    for categoria in categorias:
        print(f"{categoria[0]} - {categoria[1]}")

    escolha_categorias = input(
        "\nDigite os IDs das novas categorias separados por vírgula: "
    )

    try:

        ids_categorias = [
            int(id_categoria.strip())
            for id_categoria in escolha_categorias.split(",")
            if id_categoria.strip() != ""
        ]

    except ValueError:

        print("\nCategoria inválida!")
        conexao.close()
        return

    if len(ids_categorias) == 0:

        print("\nVocê precisa informar pelo menos uma categoria!")
        conexao.close()
        return

    ids_validos = [
        categoria[0]
        for categoria in categorias
    ]

    for id_categoria in ids_categorias:

        if id_categoria not in ids_validos:

            print(
                f"\nA categoria {id_categoria} não existe!"
            )

            conexao.close()
            return

    cursor.execute("""
        UPDATE livros

        SET
            status_id = ?,
            observacoes = ?

        WHERE id = ?
    """, (
        novo_status,
        nova_observacao,
        escolha
    ))

    cursor.execute("""
        DELETE FROM livro_categoria

        WHERE livro_id = ?
    """, (escolha,))

    for id_categoria in ids_categorias:

        cursor.execute("""
            INSERT INTO livro_categoria (
                livro_id,
                categoria_id
            )

            VALUES (?, ?)
        """, (
            escolha,
            id_categoria
        ))

    conexao.commit()
    conexao.close()

    print("\nLivro atualizado!")


# ============================================================
# MENU PRINCIPAL
# ============================================================

def menu_principal():

    while True:

        print("\n")
        print("=" * 40)
        print("          MINHA BIBLIOTECA")
        print("=" * 40)

        print("\n1 - Livros")
        print("2 - Buscar")
        print("3 - Estatísticas")
        print("4 - Configurações")
        print("5 - Sair")

        escolha = input(
            "\nEscolha uma opção: "
        )

        if escolha == "1":

            menu_livros()

        elif escolha == "2":

            menu_busca()

        elif escolha == "3":

            menu_estatisticas()

        elif escolha == "4":

            menu_configuracoes()

        elif escolha == "5":

            print("\nAté mais! 👋")
            break

        else:

            print("\nOpção inválida!")


# ============================================================
# MENU LIVROS
# ============================================================

def menu_livros():

    while True:

        print("\n")
        print("=" * 40)
        print("             LIVROS")
        print("=" * 40)

        print("\n1 - Listar livros")
        print("2 - Visualizar livro")
        print("3 - Adicionar livro")
        print("4 - Atualizar livro")
        print("5 - Deletar livro")
        print("6 - Voltar")

        escolha = input(
            "\nEscolha uma opção: "
        )

        if escolha == "1":

            listar_livros_menu()

        elif escolha == "2":

            visualizar_livro()

        elif escolha == "3":

            adicionar_livro()

        elif escolha == "4":

            atualizar_livro()

        elif escolha == "5":

            deletar_livro()

        elif escolha == "6":

            break

        else:

            print("\nOpção inválida!")


# ============================================================
# LISTAR LIVROS NO MENU
# ============================================================

def listar_livros_menu():

    livros = listar_livros()

    if len(livros) == 0:

        print("\nNão há livros cadastrados!")
        return

    print(
        "\n|============================== "
        "LIVROS "
        "==============================|"
    )

    for livro in livros:

        print(f"\nID: {livro[0]}")
        print(f"Título: {livro[1]}")
        print(f"Status: {livro[2]}")
        print(f"Categorias: {livro[3]}")

    print(
        "\n|====================================================================|"
    )


# ============================================================
# MENU BUSCA
# ============================================================

def menu_busca():

    while True:

        print("\n")
        print("=" * 40)
        print("             BUSCAR")
        print("=" * 40)

        print("\n1 - Buscar por título")
        print("2 - Buscar por categoria")
        print("3 - Buscar por status")
        print("4 - Voltar")

        escolha = input(
            "\nEscolha uma opção: "
        )

        if escolha == "1":

            buscar_por_titulo()

        elif escolha == "2":

            buscar_por_categoria()

        elif escolha == "3":

            buscar_por_status()

        elif escolha == "4":

            break

        else:

            print("\nOpção inválida!")


# ============================================================
# BUSCAR POR TÍTULO
# ============================================================

def buscar_por_titulo():

    termo = input(
        "\nDigite parte do título: "
    )

    conexao = conectar()
    cursor = conexao.cursor()

    cursor.execute("""
        SELECT
            livros.id,
            livros.titulo,
            status.nome,
            GROUP_CONCAT(categorias.nome, ', ')

        FROM livros

        LEFT JOIN status
            ON livros.status_id = status.id

        LEFT JOIN livro_categoria
            ON livros.id = livro_categoria.livro_id

        LEFT JOIN categorias
            ON livro_categoria.categoria_id = categorias.id

        WHERE livros.titulo LIKE ?

        GROUP BY
            livros.id,
            livros.titulo,
            status.nome

        ORDER BY livros.titulo
    """, (f"%{termo}%",))

    livros = cursor.fetchall()

    conexao.close()

    if len(livros) == 0:

        print("\nNenhum livro encontrado.")
        return

    print("\n|========== RESULTADOS ==========|")

    for livro in livros:

        print(f"\nID: {livro[0]}")
        print(f"Título: {livro[1]}")
        print(f"Status: {livro[2]}")
        print(f"Categorias: {livro[3]}")

    print("\n|================================|")


# ============================================================
# BUSCAR POR STATUS
# ============================================================

def buscar_por_status():

    conexao = conectar()
    cursor = conexao.cursor()

    cursor.execute("""
        SELECT id, nome

        FROM status

        ORDER BY id
    """)

    status = cursor.fetchall()

    print("\nStatus disponíveis:")

    for item in status:

        print(
            f"{item[0]} - {item[1]}"
        )

    escolha = input(
        "\nDigite o ID do status: "
    )

    try:

        status_id = int(escolha)

    except ValueError:

        print("\nID inválido!")
        conexao.close()
        return

    cursor.execute("""
        SELECT
            livros.id,
            livros.titulo,
            status.nome,
            GROUP_CONCAT(categorias.nome, ', ')

        FROM livros

        JOIN status
            ON livros.status_id = status.id

        LEFT JOIN livro_categoria
            ON livros.id = livro_categoria.livro_id

        LEFT JOIN categorias
            ON livro_categoria.categoria_id = categorias.id

        WHERE livros.status_id = ?

        GROUP BY
            livros.id,
            livros.titulo,
            status.nome

        ORDER BY livros.titulo
    """, (status_id,))

    livros = cursor.fetchall()

    conexao.close()

    if len(livros) == 0:

        print(
            "\nNenhum livro encontrado nesse status."
        )

        return

    print("\n|========== RESULTADOS ==========|")

    for livro in livros:

        print(f"\nID: {livro[0]}")
        print(f"Título: {livro[1]}")
        print(f"Status: {livro[2]}")
        print(f"Categorias: {livro[3]}")

    print("\n|================================|")


# ============================================================
# BUSCAR POR CATEGORIA
# ============================================================

def buscar_por_categoria():

    conexao = conectar()
    cursor = conexao.cursor()

    cursor.execute("""
        SELECT id, nome

        FROM categorias

        ORDER BY nome
    """)

    categorias = cursor.fetchall()

    print("\nCategorias disponíveis:")

    for categoria in categorias:

        print(
            f"{categoria[0]} - {categoria[1]}"
        )

    escolha = input(
        "\nDigite o ID da categoria: "
    )

    try:

        categoria_id = int(escolha)

    except ValueError:

        print("\nID inválido!")
        conexao.close()
        return

    cursor.execute("""
        SELECT
            livros.id,
            livros.titulo,
            status.nome,
            GROUP_CONCAT(categorias2.nome, ', ')

        FROM livros

        JOIN livro_categoria
            ON livros.id = livro_categoria.livro_id

        JOIN categorias
            ON livro_categoria.categoria_id = categorias.id

        LEFT JOIN status
            ON livros.status_id = status.id

        LEFT JOIN livro_categoria AS lc2
            ON livros.id = lc2.livro_id

        LEFT JOIN categorias AS categorias2
            ON lc2.categoria_id = categorias2.id

        WHERE categorias.id = ?

        GROUP BY
            livros.id,
            livros.titulo,
            status.nome

        ORDER BY livros.titulo
    """, (categoria_id,))

    livros = cursor.fetchall()

    conexao.close()

    if len(livros) == 0:

        print(
            "\nNenhum livro encontrado nessa categoria."
        )

        return

    print("\n|========== RESULTADOS ==========|")

    for livro in livros:

        print(f"\nID: {livro[0]}")
        print(f"Título: {livro[1]}")
        print(f"Status: {livro[2]}")
        print(f"Categorias: {livro[3]}")

    print("\n|================================|")


# ============================================================
# MENU ESTATÍSTICAS
# ============================================================

def menu_estatisticas():

    while True:

        print("\n")
        print("=" * 40)
        print("          ESTATÍSTICAS")
        print("=" * 40)

        print("\n1 - Resumo da biblioteca")
        print("2 - Livros por status")
        print("3 - Livros por categoria")
        print("4 - Voltar")

        escolha = input(
            "\nEscolha uma opção: "
        )

        if escolha == "1":

            estatisticas_resumo()

        elif escolha == "2":

            estatisticas_status()

        elif escolha == "3":

            estatisticas_categorias()

        elif escolha == "4":

            break

        else:

            print("\nOpção inválida!")


# ============================================================
# ESTATÍSTICAS - RESUMO
# ============================================================

def estatisticas_resumo():

    conexao = conectar()
    cursor = conexao.cursor()

    cursor.execute("""
        SELECT COUNT(*)
        FROM livros
    """)

    total_livros = cursor.fetchone()[0]

    cursor.execute("""
        SELECT COUNT(*)
        FROM categorias
    """)

    total_categorias = cursor.fetchone()[0]

    cursor.execute("""
        SELECT COUNT(*)
        FROM status
    """)

    total_status = cursor.fetchone()[0]

    conexao.close()

    print("\n|========== RESUMO ==========|")

    print(
        f"\n📚 Livros cadastrados: "
        f"{total_livros}"
    )

    print(
        f"🏷️ Categorias cadastradas: "
        f"{total_categorias}"
    )

    print(
        f"📋 Status disponíveis: "
        f"{total_status}"
    )

    print("\n|=============================|")


# ============================================================
# ESTATÍSTICAS - STATUS
# ============================================================

def estatisticas_status():

    conexao = conectar()
    cursor = conexao.cursor()

    cursor.execute("""
        SELECT
            status.nome,
            COUNT(livros.id)

        FROM status

        LEFT JOIN livros
            ON livros.status_id = status.id

        GROUP BY
            status.id,
            status.nome

        ORDER BY status.id
    """)

    resultados = cursor.fetchall()

    conexao.close()

    print("\n|======= LIVROS POR STATUS =======|")

    for resultado in resultados:

        print(
            f"\n{resultado[0]}: "
            f"{resultado[1]}"
        )

    print("\n|=================================|")


# ============================================================
# ESTATÍSTICAS - CATEGORIAS
# ============================================================

def estatisticas_categorias():

    conexao = conectar()
    cursor = conexao.cursor()

    cursor.execute("""
        SELECT
            categorias.nome,
            COUNT(livro_categoria.livro_id)

        FROM categorias

        LEFT JOIN livro_categoria
            ON categorias.id = livro_categoria.categoria_id

        GROUP BY
            categorias.id,
            categorias.nome

        ORDER BY
            COUNT(livro_categoria.livro_id) DESC,
            categorias.nome
    """)

    resultados = cursor.fetchall()

    conexao.close()

    print(
        "\n|======= LIVROS POR CATEGORIA =======|"
    )

    for resultado in resultados:

        print(
            f"\n{resultado[0]}: "
            f"{resultado[1]}"
        )

    print(
        "\n|=====================================|"
    )


# ============================================================
# LISTAR CATEGORIAS
# ============================================================

def listar_categorias():

    conexao = conectar()
    cursor = conexao.cursor()

    cursor.execute("""
        SELECT id, nome

        FROM categorias

        ORDER BY nome
    """)

    categorias = cursor.fetchall()

    conexao.close()

    print("\n|========== CATEGORIAS ==========|")

    for categoria in categorias:

        print(
            f"{categoria[0]} - "
            f"{categoria[1]}"
        )

    print("\n|================================|")


# ============================================================
# ADICIONAR CATEGORIA
# ============================================================

def adicionar_categoria():

    nome = input(
        "\nNome da nova categoria: "
    ).strip()

    if nome == "":

        print(
            "\nO nome da categoria não pode ficar vazio!"
        )

        return

    conexao = conectar()
    cursor = conexao.cursor()

    cursor.execute("""
        SELECT id

        FROM categorias

        WHERE nome = ?
    """, (nome,))

    categoria = cursor.fetchone()

    if categoria is not None:

        print(
            "\nEssa categoria já existe!"
        )

        conexao.close()
        return

    cursor.execute("""
        INSERT INTO categorias (nome)

        VALUES (?)
    """, (nome,))

    conexao.commit()
    conexao.close()

    print(
        f"\nCategoria '{nome}' adicionada!"
    )


# ============================================================
# MENU CATEGORIAS
# ============================================================

def menu_categorias():

    while True:

        print("\n")
        print("=" * 40)
        print("        CATEGORIAS")
        print("=" * 40)

        print("\n1 - Listar categorias")
        print("2 - Adicionar categoria")
        print("3 - Voltar")

        escolha = input(
            "\nEscolha uma opção: "
        )

        if escolha == "1":

            listar_categorias()

        elif escolha == "2":

            adicionar_categoria()

        elif escolha == "3":

            break

        else:

            print("\nOpção inválida!")


# ============================================================
# MENU CONFIGURAÇÕES
# ============================================================

def menu_configuracoes():

    while True:

        print("\n")
        print("=" * 40)
        print("          CONFIGURAÇÕES")
        print("=" * 40)

        print("\n1 - Gerenciar categorias")
        print("2 - Gerenciar status")
        print("3 - Informações do banco")
        print("4 - Voltar")

        escolha = input(
            "\nEscolha uma opção: "
        )

        if escolha == "1":

            menu_categorias()

        elif escolha == "2":

            listar_status()

        elif escolha == "3":

            informacoes_banco()

        elif escolha == "4":

            break

        else:

            print("\nOpção inválida!")


# ============================================================
# LISTAR STATUS
# ============================================================

def listar_status():

    conexao = conectar()
    cursor = conexao.cursor()

    cursor.execute("""
        SELECT id, nome

        FROM status

        ORDER BY id
    """)

    status = cursor.fetchall()

    conexao.close()

    print("\n|========== STATUS ==========|")

    for item in status:

        print(
            f"{item[0]} - "
            f"{item[1]}"
        )

    print("\n|============================|")


# ============================================================
# INFORMAÇÕES DO BANCO
# ============================================================

def informacoes_banco():

    conexao = conectar()
    cursor = conexao.cursor()

    cursor.execute("""
        SELECT COUNT(*)
        FROM livros
    """)

    total_livros = cursor.fetchone()[0]

    cursor.execute("""
        SELECT COUNT(*)
        FROM categorias
    """)

    total_categorias = cursor.fetchone()[0]

    cursor.execute("""
        SELECT COUNT(*)
        FROM livro_categoria
    """)

    total_relacoes = cursor.fetchone()[0]

    caminho = obter_caminho_banco()

    conexao.close()

    print(
        "\n|======= INFORMAÇÕES DO BANCO =======|"
    )

    print(
        f"\n🗄️ Banco: {caminho}"
    )

    print(
        f"📚 Livros: {total_livros}"
    )

    print(
        f"🏷️ Categorias: {total_categorias}"
    )

    print(
        f"🔗 Relações livro-categoria: "
        f"{total_relacoes}"
    )

    print(
        "\n|====================================|"
    )


# ============================================================
# INÍCIO DO PROGRAMA
# ============================================================

if __name__ == "__main__":

    print("\n")
    print("=" * 50)
    print("       CAMINHO DO BANCO DE DADOS")
    print("=" * 50)

    print(
        obter_caminho_banco()
    )

    print("=" * 50)

    menu_principal()
