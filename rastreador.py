import os
import json
import requests

TOKEN = os.environ["TELEGRAM_TOKEN"]
CHAT_ID = os.environ["TELEGRAM_CHAT_ID"]

ARQUIVO_PRODUTOS = "produtos.json"
ARQUIVO_HISTORICO = "historico_precos.json"

# Critérios de qualidade do vendedor: só aceitamos produtos
# de lojas nesses tipos E com nota igual ou maior que a mínima.
TIPOS_LOJA_ACEITOS = {"mall", "star", "star_plus"}
NOTA_MINIMA = 4.8


def carregar_json(caminho):
    """Lê um arquivo JSON e devolve o conteúdo como um dicionário Python."""
    with open(caminho, "r", encoding="utf-8") as arquivo:
        return json.load(arquivo)


def salvar_json(caminho, dados):
    """Salva um dicionário Python de volta no arquivo JSON."""
    with open(caminho, "w", encoding="utf-8") as arquivo:
        json.dump(dados, arquivo, indent=2, ensure_ascii=False)


def enviar_mensagem(texto):
    """Envia uma mensagem de texto para o canal do Telegram."""
    url = f"https://api.telegram.org/bot{TOKEN}/sendMessage"
    dados = {
        "chat_id": CHAT_ID,
        "text": texto,
        "parse_mode": "HTML",
        "disable_web_page_preview": False,
    }
    resposta = requests.post(url, data=dados)
    if resposta.status_code != 200:
        print(f"Erro ao enviar mensagem: {resposta.text}")


def vendedor_aprovado(produto):
    """Verifica se a loja do produto atende aos critérios mínimos de qualidade."""
    tipo_ok = produto["loja_tipo"] in TIPOS_LOJA_ACEITOS
    nota_ok = produto["loja_nota"] >= NOTA_MINIMA
    return tipo_ok and nota_ok


def montar_mensagem(produto, preco_antigo, preco_novo):
    """Monta o texto do alerta de queda de preço, já com o aviso de publicidade exigido pelo CONAR."""
    desconto_percentual = ((preco_antigo - preco_novo) / preco_antigo) * 100

    texto = (
        f"📉 <b>BAIXOU DE PREÇO!</b>\n\n"
        f"🔧 {produto['nome']}\n"
        f"De: <s>R$ {preco_antigo:.2f}</s>\n"
        f"Por: <b>R$ {preco_novo:.2f}</b> (-{desconto_percentual:.0f}%)\n\n"
        f"🔗 {produto['link_afiliado']}\n\n"
        f"#Publicidade | Link de afiliado"
    )
    return texto


def main():
    produtos = carregar_json(ARQUIVO_PRODUTOS)["produtos"]
    historico = carregar_json(ARQUIVO_HISTORICO)

    for produto in produtos:
        id_produto = produto["id"]

        # Primeiro filtro: o vendedor passa nos critérios de qualidade?
        if not vendedor_aprovado(produto):
            print(f"Pulando '{produto['nome']}': vendedor não atende aos critérios de qualidade.")
            continue  # "continue" pula pro próximo produto, sem fazer mais nada com este

        preco_novo = produto["preco_atual"]
        preco_antigo = historico.get(id_produto)  # None se for a primeira vez que vemos esse produto

        if preco_antigo is None:
            print(f"Primeira vez vendo '{produto['nome']}'. Guardando preço R$ {preco_novo:.2f}.")
        elif preco_novo < preco_antigo:
            print(f"Preço caiu! '{produto['nome']}': R$ {preco_antigo:.2f} -> R$ {preco_novo:.2f}")
            mensagem = montar_mensagem(produto, preco_antigo, preco_novo)
            enviar_mensagem(mensagem)
        else:
            print(f"Sem novidade para '{produto['nome']}' (R$ {preco_novo:.2f}).")

        # Atualiza o histórico com o preço de hoje, para a próxima comparação
        historico[id_produto] = preco_novo

    salvar_json(ARQUIVO_HISTORICO, historico)


if __name__ == "__main__":
    main()
