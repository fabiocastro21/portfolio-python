# ⚔️ Aventura Python - 3 Dungeons (3D)

Jogo de aventura e ação em 3D desenvolvido em **Python** utilizando a engine **Ursina** e o motor gráfico **Panda3D**. O jogador explora um mundo aberto (Overworld) e deve enfrentar hordas de inimigos em 3 dungeons progressivas, desbloqueando habilidades especiais e enfrentando chefes únicos.

---

## 📸 Visão Geral e Mecânicas

- **Mundo Aberto (Overworld):** Campo aberto com iluminação, terreno com texturas repetidas e portas de acesso às Dungeons.
- **Dungeons Progressivas:** 3 fases temáticas distintas (*Floresta*, *Fogo* e *Água*), cada uma com texturas de chão, parede e teto personalizadas.
- **Sistema de Combate & Habilidades:**
  - **Ataque Básico de Espada:** Ataque frontal em alcance direto.
  - **Ataque Giratório (Spin Attack):** Desbloqueado ao completar a Dungeon 1. Permite carregar o ataque para atingir todos os inimigos ao redor com repelimento (Knockback).
  - **Escudo de Defesa (Block):** Desbloqueado ao completar a Dungeon 2. Reduz/anula danos e atordoa inimigos no contra-ataque.
- **Projéteis & IA de Inimigos:**
  - Inimigos normais de patrulha e perseguidores.
  - Chefes únicos por dungeon com padrões de ataque específicos (Dashes rápidos, lançamento de Projéteis/Bolas de Fogo e combinações).
- **Sistema de Bônus & Vidas Extra:** Concluir uma dungeon sem sofrer dano (*Perfeição*) concede +1 vida extra.
- **Eventos Automáticos:** Sistema de respawn dinâmico de inimigos por inatividade no mapa aberto.
- **Câmera Inteligente:** Sistema de colisão de câmera com paredes para transparência automática de estruturas no campo de visão.

---

## 🎮 Controles

| Tecla / Comando | Ação |
| :--- | :--- |
| **W, A, S, D** / **Setas** | Movimentação do Personagem |
| **Mouse** | Controle de Câmera 3D (Look) |
| **Clique Esquerdo (Pressionar/Segurar)** | Ataque Simples / Carregar Ataque Giratório |
| **Clique Direito** / **Shift** | Defender com Escudo |
| **ENTER** | Iniciar Jogo / Entrar na Dungeon |
| **R** | Reiniciar (Tela de Game Over / Vitória) |
| **ESC** | Bloquear / Travar o Cursor do Mouse |

---

## 🛠️ Tecnologias Utilizadas

- **Linguagem:** Python 3.7+
- **Game Engine:** [Ursina Engine](https://www.ursinengine.org/)
- **Renderizador 3D:** Panda3D
- **Sistemas Nativo:** Leitura dinâmica de diretórios/executável (`sys.frozen`, `os.path`)
- **Assets:** Texturas customizadas (PNG) e Modelagem Procedural em código.

---

## 🚀 Como Executar o Jogo

1. **Instale as dependências necessárias:**
   ```bash
   pip install ursina panda3d
