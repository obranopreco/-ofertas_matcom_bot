name: Rastreador de Ofertas

on:
  workflow_dispatch:
  schedule:
    - cron: "0 * * * *"

jobs:
  checar-precos:
    runs-on: ubuntu-latest

    steps:
      - name: Baixar código
        uses: actions/checkout@v4

      - name: Configurar Python
        uses: actions/setup-python@v5
        with:
          python-version: "3.11"

      - name: Instalar dependências
        run: pip install requests

      - name: Executar rastreador
        env:
          TELEGRAM_TOKEN: ${{ secrets.TELEGRAM_TOKEN }}
          TELEGRAM_CHAT_ID: ${{ secrets.TELEGRAM_CHAT_ID }}
          SHOPEE_APP_ID: ${{ secrets.SHOPEE_APP_ID }}
          SHOPEE_APP_SECRET: ${{ secrets.SHOPEE_APP_SECRET }}
        run: python rastreador.py

      - name: Salvar histórico atualizado
        run: |
          echo "=== Conteúdo do ofertas_recentes.json ==="
          cat ofertas_recentes.json
          echo "========================================="
          git config user.name "Rastreador Bot"
          git config user.email "bot@rastreador.local"
          git add historico_precos.json ofertas_recentes.json
          git diff --staged --quiet || git commit -m "Atualiza histórico de preços"
          git push
