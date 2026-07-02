import os
import json
import requests
from datetime import datetime

from shopee_api import buscar_produtos_shopee

TOKEN = os.environ["TELEGRAM_TOKEN"]
CHAT_ID = os.environ["TELEGRAM_CHAT_ID"]

ARQUIVO_PALAVRAS_CHAVE = "palavras_chave.json"
ARQUIVO_HISTORICO = "historico_precos.json"
ARQUIVO_OFERTAS = "ofertas_recentes.json"

TIPOS_LOJA_ACEITOS = {1, 4, 5}
NOTA_MINIMA = 0  # sem filtro de nota, aceita todos os vendedores

DESCONTO_MINIMO_PERCENTUAL = 5
MAX_OFERTAS_RECENTES = 20  # quantas ofertas manter no arquivo do site


def carregar_json(caminho):
    with open(caminho, "r", encoding="utf-8") as arquivo:
        return json.load(arquivo)


def salvar_json(caminho, dados):
    with open(caminho, "w", encoding="utf-8") as arquivo:
        json.dump(dados, arquivo, indent=2, ensure_ascii=False)


def enviar_mensagem(texto):
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


def salvar_oferta_site(produto, preco_antigo, preco_novo):
    """Salva a oferta detectada no arquivo que o site WordPress vai ler."""
    desconto_percentual = ((preco_antigo - preco_novo) / preco_antigo) * 100

    # Tenta carregar ofertas existentes; se o arquivo não existir, começa do zero
    try:
        ofertas = carregar_json(ARQUIVO_OFERTAS)
    except FileNotFoundError:
        ofertas = []

    # Monta o objeto da nova oferta
    nova_oferta = {
        "id": str(produto["itemId"]),
        "nome": produto["productName"],
        "imagem": produto.get("imageUrl", ""),
        "preco_antigo": round(preco_antigo, 2),
        "preco_novo": round(preco_novo, 2),
        "desconto_percentual": round(desconto_percentual, 0),
        "link_afiliado": produto["offerLink"],
        "detectada_em": datetime.utcnow().strftime("%d/%m/%Y %H:%M UTC")
    }

    # Remove essa oferta se já existia antes (pra evitar duplicata)
    ofertas = [o for o in ofertas if o["id"] != nova_oferta["id"]]

    # Adiciona a nova oferta no topo da lista
    ofertas.insert(0, nova_oferta)

    # Mantém só as últimas MAX_OFERTAS_RECENTES
    ofertas = ofertas[:MAX_OFERTAS_RECENTES]

    salvar_json(ARQUIVO_OFERTAS, ofertas)
    print(f"  -> Oferta salva em '{ARQUIVO_OFERTAS}' para exibir no site.")


def vendedor_aprovado(produto):
    nota_bruta = produto.get("ratingStar")
    nota = float(nota_bruta) if nota_bruta else 0
    return nota >= NOTA_MINIMA


def montar_mensagem(produto, preco_antigo, preco_novo):
    desconto_percentual = ((preco_antigo - preco_novo) / preco_antigo) * 100
    texto = (
        f"📉 <b>BAIXOU DE PREÇO!</b>\n\n"
        f"🔧 {produto['productName']}\n"
        f"De: <s>R$ {preco_antigo:.2f}</s>\n"
        f"Por: <b>R$ {preco_novo:.2f}</b> (-{desconto_percentual:.0f}%)\n\n"
        f"🔗 {produto['offerLink']}\n\n"
        f"#Publicidade | Link de afiliado"
    )
    return texto


def main():
    palavras_chave = carregar_json(ARQUIVO_PALAVRAS_CHAVE)["palavras_chave"]
    historico = carregar_json(ARQUIVO_HISTORICO)

    for palavra in palavras_chave:
        print(f"\nBuscando: '{palavra}'...")
        produtos = buscar_produtos_shopee(palavra, limite=10)
        print(f"  -> A API retornou {len(produtos)} produto(s) para essa busca.")

        for produto in produtos:
            id_produto = str(produto["itemId"])
            nome_produto = produto["productName"]

            if not vendedor_aprovado(produto):
                continue

            preco_novo = float(produto["priceMin"])
            preco_antigo = historico.get(id_produto)

            if preco_antigo is None:
                print(f"Primeira vez vendo '{nome_produto}'. Guardando preco R$ {preco_novo:.2f}.")
            else:
                queda_percentual = ((preco_antigo - preco_novo) / preco_antigo) * 100
                if preco_novo < preco_antigo and queda_percentual >= DESCONTO_MINIMO_PERCENTUAL:
                    print(f"Oferta real! '{nome_produto}': R$ {preco_antigo:.2f} -> R$ {preco_novo:.2f}")
                    mensagem = montar_mensagem(produto, preco_antigo, preco_novo)
                    enviar_mensagem(mensagem)
                    salvar_oferta_site(produto, preco_antigo, preco_novo)
                else:
                    print(f"Sem oferta relevante para '{nome_produto}' (R$ {preco_novo:.2f}).")

            historico[id_produto] = preco_novo

    salvar_json(ARQUIVO_HISTORICO, historico)


if __name__ == "__main__":
    main()
