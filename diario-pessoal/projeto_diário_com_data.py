import json

from datetime import datetime

from zoneinfo import ZoneInfo

def main():
    while True:
      print(' ')
      print(' ')

      print('|---------------------------|')
      print('|          \033[1;30mMENU\033[0m             |') # código Ansi para formatação, o 18 é a cor e o 1 é o estilo(negrito)#
      print('|---------------------------|')
      print('|    1. Nova entrada        |')
      print('|    2. Ver diário          |')
      print('|    3. Deletar entrada     |')
      print('|    4. Sair                |')
      print('|---------------------------|')
      print(' ')
      opcaomenu = int(input('Escolha sua opção: '))

      if opcaomenu == 1:
        menu1()

      elif opcaomenu == 2:
        continuar = menu2()
        if continuar == False:
          menu4()
          break

      elif opcaomenu == 3:
        menu3()

      elif opcaomenu == 4:
        menu4()
        break
      else:
        print('Opção inválida!')

def menu1():
  agora = datetime.now(ZoneInfo("America/Sao_Paulo"))

  data_formatada = agora.strftime("%d/%m/%Y %H:%M")

  with open("diario.json", "r", encoding="utf-8-sig") as arquivo:
    dados = json.load(arquivo)

  texto = (input("Escreva sua entrada: "))

  if len(dados) == 0:
    novo_id = 1
  else:
    novo_id = max((entrada["id"] for entrada in dados)) + 1

  nova_entrada = {
      "id":novo_id,
      "data": data_formatada,
      'texto' : texto}

  dados.append(nova_entrada)

  with open("diario.json", "w", encoding="utf-8") as arquivo:
    json.dump(dados, arquivo, indent=4, ensure_ascii=False)# pra aceitar todos os tipos de caracteres#

  print(' ')
  print("Entrada salva!")


def menu2():
  with open("diario.json", "r", encoding="utf-8-sig") as arquivo:
    dados = json.load(arquivo)
  visualise(dados)
  print(' ')
  if len(dados) == 0:

    voltar = int(input("Voltar ao menu principal? [1 - Sim / 2 - Não (Fechar o programa) ] "))

    if voltar == 2:
      return False
    elif voltar == 1:
      pass
    else:
      while voltar != 1 and voltar != 2:
        print(' ')
        print('Opção inválida!')
        voltar = int(input("Voltar ao menu principal? [1 - Sim / 2 - Não] "))
        print(' ')
        if voltar ==2:
          return False

  return True



def visualise(dados):
  if len(dados) == 0:
    print(' ')
    print('Não há entradas no seu diário!')

  else:
    print("\n|========== ENTRADAS ==========|")


    for entrada in dados:
        print(f"{entrada['id']} - {entrada['data']}")

    escolha = int(input("\nDigite o ID da entrada que deseja ler: "))

    for entrada in dados:
        if entrada["id"] == escolha:
            print("\n|========== ENTRADA ==========|")
            print(' ')
            print(f"Data: {entrada['data']}")
            print(f"\n{entrada['texto']}")
            print(' ')
            print("|==============================|")
            return

    print(' ')
    print("Entrada não encontrada.")


def delete(dados):
  if len(dados) == 0:
    print(' ')
    print('Não há entradas no seu diário!')

  else:
    print("\n|========== ENTRADAS ==========|")

    for entrada in dados:
      print(f"{entrada['id']} - {entrada['data']}")

    escolha = int(input("\nDigite o ID da entrada que deseja deletar: "))

    for indice, entrada in enumerate(dados):

      if entrada["id"] == escolha:
        del dados[indice]

        with open("diario.json", "w", encoding="utf-8") as arquivo:
          json.dump(dados, arquivo, indent=4, ensure_ascii=False)

        print(' ')
        print("Entrada deletada!")
        return

    print(' ')
    print('Entrada não encontrada!')

def menu3():
  with open("diario.json", "r", encoding="utf-8-sig") as arquivo:
    dados = json.load(arquivo)

  delete(dados)

def menu4():
  print(' ')
  print(' O diário será fechado! Até a próxima!')

main()
