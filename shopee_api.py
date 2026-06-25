import os
import time
import json
import hashlib
import requests

APP_ID = os.environ["SHOPEE_APP_ID"]
APP_SECRET = os.environ["SHOPEE_APP_SECRET"]

URL_BASE = "https://open-api.affiliate.shopee.com.br/graphql"


def gerar_assinatura(timestamp, payload):
    """
    Monta a assinatura exigida pela Shopee.
    Fórmula oficial: SHA256(AppId + Timestamp + Payload + Secret)
    Tudo concatenado em texto, sem espaços ou separadores entre as partes.
    """
    texto_para_hash = f"{APP_ID}{timestamp}{payload}{APP_SECRET}"
    return hashlib.sha256(texto_para_hash.encode("utf-8")).hexdigest()


def buscar_produtos_shopee(palavra_chave, limite=20):
    """
    Busca produtos na Shopee usando o endpoint productOfferV2,
    filtrando por tipo de loja (Mall, Star, Star+) direto na consulta.
    listType: 1 = Mall, conforme documentação. Vamos filtrar por nota no nosso código depois.
    """
    query_graphql = """
    {
      productOfferV2(
        keyword: "%s",
        sortType: 5,
        page: 1,
        limit: %d
      ) {
        nodes {
          itemId
          productName
          offerLink
          imageUrl
          priceMin
          priceMax
          priceDiscountRate
          ratingStar
          commissionRate
          shopId
          shopName
          shopType
        }
        pageInfo {
          page
          limit
          hasNextPage
        }
      }
    }
    """ % (palavra_chave, limite)

    # O "payload" usado na assinatura é exatamente o corpo (body) que vamos enviar,
    # já transformado em texto JSON -- por isso montamos ele antes de assinar.
    corpo_requisicao = {"query": query_graphql}
    payload_texto = json.dumps(corpo_requisicao, ensure_ascii=False)

    timestamp = int(time.time())  # tempo atual em segundos (Unix time)
    assinatura = gerar_assinatura(timestamp, payload_texto)

    headers = {
        "Content-Type": "application/json",
        "Authorization": f"SHA256 Credential={APP_ID}, Timestamp={timestamp}, Signature={assinatura}",
    }

    resposta = requests.post(URL_BASE, headers=headers, data=payload_texto.encode("utf-8"))

    if resposta.status_code != 200:
        print(f"Erro na requisição: {resposta.status_code} - {resposta.text}")
        return []

    dados = resposta.json()

    # Se a Shopee devolveu algum erro de negócio (ex: assinatura inválida),
    # ele aparece dentro do JSON, mesmo com status_code 200.
    if "errors" in dados:
        print(f"Erro retornado pela API: {dados['errors']}")
        return []

    produtos = dados["data"]["productOfferV2"]["nodes"]
    return produtos


if __name__ == "__main__":
    # Teste rápido: busca produtos com a palavra-chave "furadeira"
    resultados = buscar_produtos_shopee("furadeira", limite=5)
    print(f"Encontrados {len(resultados)} produtos:")
    for produto in resultados:
        print(f"- {produto['productName']} | R$ {produto['priceMin']} | nota {produto['ratingStar']} | tipo {produto['shopType']}")
