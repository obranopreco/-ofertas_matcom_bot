import os
import requests

TOKEN = os.environ["TELEGRAM_TOKEN"]
CHAT_ID = os.environ["TELEGRAM_CHAT_ID"]

def enviar_mensagem(texto):
    url = f"https://api.telegram.org/bot{TOKEN}/sendMessage"
    dados = {
        "chat_id": CHAT_ID,
        "text": texto,
        "parse_mode": "HTML",
    }
    resposta = requests.post(url, data=dados)
    if resposta.status_code == 200:
        print("Mensagem enviada com sucesso!")
    else:
        print(f"Erro ao enviar mensagem: {resposta.text}")

if __name__ == "__main__":
    enviar_mensagem("🤖 Teste automático via GitHub Actions! Se você está vendo isso, funcionou.")
