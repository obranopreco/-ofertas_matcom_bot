import os
import requests

# O token e o ID do canal NÃO ficam escritos aqui no código.
# Eles vêm de "variáveis de ambiente" -- valores guardados
# de forma segura no GitHub (vamos configurar isso no próximo passo).
TOKEN = os.environ["TELEGRAM_TOKEN"]
CHAT_ID = os.environ["TELEGRAM_CHAT_ID"]


def enviar_mensagem(texto):
    """Envia uma mensagem de texto para o canal do Telegram."""
    url = f"https://api.telegram.org/bot{TOKEN}/sendMessage"
    dados = {
        "chat_id": CHAT_ID,
        "text": texto,
        "parse_mode": "HTML",  # permite usar <b>negrito</b>, <a href="">links</a>, etc
    }
    resposta = requests.post(url, data=dados)

    if resposta.status_code == 200:
        print("Mensagem enviada com sucesso!")
    else:
        print(f"Erro ao enviar mensagem: {resposta.text}")


# Esse bloco só roda quando executamos este arquivo diretamente
if __name__ == "__main__":
    enviar_mensagem("🤖 Teste automático via GitHub Actions! Se você está vendo isso, funcionou.")
