# PAYER-FIRST 003 — CASH-FIRST RECONCILIATION (READ-ONLY)

**Data:** 18-11-2026. **Resultado:** 31/31 testes locais PASS, 16 entradas ledger sintéticas, 17 eventos sintéticos, 2 correspondências de exemplo e 14 exceções. **ZERO pagamentos reais, clientes ou lucros.**

- Resultado económico: **NO-GO** para SaaS genérico de pagamentos/reconciliação; fornecedores estabelecidos já oferecem isto (Request Finance, Bitwave, Cryptio, Coinbase CDP).
- Possível próximo gate: **GO condicional para entrevistas comerciais** sobre serviço de revisão de exceções entre sistemas e reconciliação de fecho, antes de desenvolver outra aplicação.
- Dados completamente inventados com hashes determinísticos; contrato USDC Base corresponde a endereço oficial Circle mas transações não existem.
- Detalhe: duplo-claim de uma transferência para duas faturas é bloqueado; não há auto-match sem referência vinculativa; token, rede, 6 decimais, direções, origens, destinos, valor, logs, confirmação, status e origem não autenticada são todos controlados.
- Material completo: [ZIP de código, testes, dashboard, relatórios e SHA256SUMS no Google Drive](https://drive.google.com/file/d/1-dQ-wL4nfhpV1aKRIePBryu3n5NjS9KT/view?usp=drivesdk). SHA256 ZIP: `fb4013f739f2cf2bcf2d86078d43a8d2897c08e929adedf4d9366f3239c33527`.
- Relatório de investigação: [Drive](https://docs.google.com/document/d/1auitr8mk33a8AEhN68SZpoZ5fWCo7Z5j7pZNJCs4jyo/edit?usp=drivesdk).

**Caveats:** sem RPC real, sem dados de clientes, sem contabilidade certificada, sem garantias de finality, sem ERP, sem contas, sem licenciamento analisado, sem transações, fundos, custo ou contacto externo. Os testes foram executados LOCALMENTE, não em GitHub CI. PR permanece draft e sem merge para main. Nenhum dado holdout de trading foi tocado.

Fontes: [Request Finance](https://www.requestfinance.com/pricing) · [Bitwave](https://www.bitwave.io/) · [Cryptio](https://cryptio.co/solutions/reconciliation) · [Circle USDC Base](https://www.circle.com/blog/usdc-now-available-natively-on-base) · [Caliza job](https://jobs.lever.co/caliza-financial-technologies/2b242a88-7660-4e90-b3a9-cb5ade877270).


## Como recuperar a versão de código auditada armazenada no GitHub

O conteúdo completo do ZIP foi arquivado em `PAYER_FIRST_003_READONLY_ZIP.base64` no mesmo diretório por limitações do conector de ficheiros binários. É um arquivo **Base64**, não um script. Depois de descarregar o ficheiro, executa localmente:

```bash
base64 --decode PAYER_FIRST_003_READONLY_ZIP.base64 > PAYER_FIRST_003_CASH_FIRST_READONLY.zip
sha256sum PAYER_FIRST_003_CASH_FIRST_READONLY.zip
unzip PAYER_FIRST_003_CASH_FIRST_READONLY.zip
cd payer_first_003
python -m unittest -q test_reconcile.py
```

SHA-256 esperado do ZIP: `fb4013f739f2cf2bcf2d86078d43a8d2897c08e929adedf4d9366f3239c33527`. O ZIP descarregado diretamente do Drive é a alternativa mais simples. O GitHub armazena os mesmos bytes codificados; **não** foi executado CI GitHub.
