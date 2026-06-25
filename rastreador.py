import os
import json
import requests

from shopee_api import buscar_produtos_shopee

TOKEN = os.environ["TELEGRAM_TOKEN"]
CHAT_ID = os.environ["TELEGRAM_CHAT_ID"]

ARQUIVO_PALAVRAS_CHAVE = "palavras_chave.json"
ARQUIVO_HISTORICO = "historico_precos.json"

# Critérios de qualidade do vendedor: só aceitamos produtos
# de lojas nesses tipos E com nota igual ou maior que a mínima.
TIPOS_LOJA_ACEITOS = {1, 4, 5}  # Mall, Star, Star+ (conforme shopType da API)
NOTA_MINIMA = 4.8

# Queda mínima para considerar "oferta" e disparar alerta (evita alertar por R$0,01)
DESCONTO_MINIMO_PERCENTUAL = 5


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


def vendedor_aprovado(produto):
    """Verifica se a loja do produto atende aos criterios minimos de qualidade."""
    tipos_da_loja = produto.get("shopType") or []
    tipo_ok = any(tipo in TIPOS_LOJA_ACEITOS for tipo in tipos_da_loja)
    # ratingStar pode vir como texto (ex: "4.9") em vez de número, então convertemos
    nota_bruta = produto.get("ratingStar")
    nota = float(nota_bruta) if nota_bruta else 0
    nota_ok = nota >= NOTA_MINIMA
    return tipo_ok and nota_ok


def montar_mensagem(produto, preco_antigo, preco_novo):
    """Monta o texto do alerta de queda de preco, ja com o aviso de publicidade exigido pelo CONAR."""
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
                print(f"  [REPROVADO] '{nome_produto}' -- shopType={produto.get('shopType')}, ratingStar={produto.get('ratingStar')}")
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
                else:
                    print(f"Sem oferta relevante para '{nome_produto}' (R$ {preco_novo:.2f}).")

            historico[id_produto] = preco_novo

    salvar_json(ARQUIVO_HISTORICO, historico)


if __name__ == "__main__":
    main()
