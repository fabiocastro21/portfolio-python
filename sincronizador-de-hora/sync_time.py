import requests
import os
import datetime

try:
    # Ajuste inicial para evitar erro de certificado (data fixa confiavel)
    dt_fallback = datetime.datetime(2026, 9, 1, 0, 0, 0)
    os.system(f"powershell -Command \"Set-Date -Date '{dt_fallback}'\"")
    print("Relogio ajustado inicialmente para:", dt_fallback)

    # Consulta a API de hora
    response = requests.get("https://timeapi.io/api/Time/current/zone?timeZone=America/Sao_Paulo")
    data = response.json()

    # Corrige microssegundos longos
    dt_str = data["dateTime"].split(".")[0]
    dt = datetime.datetime.fromisoformat(dt_str)

    # Ajusta relogio para a hora real
    os.system(f"powershell -Command \"Set-Date -Date '{dt}'\"")
    print("Relogio atualizado com sucesso para:", dt)

except Exception as e:
    print("Erro ao atualizar:", e)

finally:
    input("Pressione Enter para sair...")

