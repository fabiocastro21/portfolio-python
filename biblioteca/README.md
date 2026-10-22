
# 📚 Gerenciador de Biblioteca Desktop (GUI)

Aplicativo desktop completo para gerenciamento de acervo pessoal de livros, controle de leitura e estatísticas.

O projeto foi originalmente construído para execução via terminal (DOS) e posteriormente migrado para uma **Interface Gráfica (GUI)** amigável com suporte ao **Windows 7 (32-bits)** e versões superiores.

---

## ✨ Funcionalidades

- **Gerenciamento de Livros (CRUD):**
  - Cadastro, edição completa, exclusão com confirmação e visualização de detalhes.
  - Vínculo de múltiplas categorias por livro (Relacionamento N:N).
  - Campo dedicado para observações e anotações.

- **Busca e Filtros Combinados:**
  - Pesquisa por título (palavra-chave).
  - Filtro combinável por **Status de Leitura** (*não lido, lendo, lido, consulta*) e por **Categoria**.
  - Ordenação dinâmica (A-Z, Z-A, ID) ao clicar nos cabeçalhos das colunas.

- **Painel de Estatísticas:**
  - Resumo de livros cadastrados, categorias e relacionamentos.
  - Relatórios de distribuição de livros por status e ranking por categoria.

---

## 🛠️ Tecnologias Utilizadas

- **Linguagem:** Python 3.7+
- **Interface Gráfica (GUI):** Tkinter / `ttk` (Nativo)
- **Banco de Dados:** SQLite3
- **Compilação:** PyInstaller (Executável standalone `.exe`)

---

## 🏗️ Arquitetura do Código

- `banco.py`: Camada de dados e regras de negócio SQL (SQLite, `JOIN`, `GROUP_CONCAT`, agregações).
- `app_gui.py`: Camada de apresentação gráfica desenvolvida em Tkinter com gerenciamento de abas e eventos.
