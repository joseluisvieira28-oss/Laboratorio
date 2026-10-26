# Crypto Lab — Fusion Radar Visual + Science Gate V0.3.2

**Estado em 26/10/2026: visualização operacional / histórico Multi-Asset SOURCE_INCOMPLETE / SEM PNL / NO LIVE GO.**

## A. TradingView
Copiar o ficheiro `Fusion_Radar_Visual_V032.pine` na totalidade para o Pine Editor (começa na coluna 1 com `//@version=6`), guardar, selecionar 1H, adicionar ao gráfico. Por exemplo, `BINANCE:SOLUSDT.P`.

- Painel BTC20 vs tendência do ativo de 20 dias: AVAX, SOL, ETH, BNB, XRP, LINK.
- D1 confirmado `close[1]` vs `close[21]`, `barmerge.lookahead_on` para evitar fuga de informação do fecho do dia corrente.
- Marcadores F+/F− apenas para o ativo em exibição, na vela das **01:00 UTC**; sem faixas verticais. O `low`/`high` da vela é apenas posição visual, não preço de execução.
- 12 condições de alerta por ativo/novo estado (6 × F+ ou F-), sem ordens. No TradingView escolher **Once Per Bar**; há latência dependente dos ticks e dos serviços.
- Indicador VISUAL: intencionalmente **sem N/DIAS, NET14/NET20, DD14 ou promessas de edge**. Fonte errada ou sem dados fica como SEM DADOS.
- Não compilado dentro da sessão do utilizador nesta execução: os testes locais são estáticos, não um teste do compilador TradingView.

## B. Laboratório científico Python separado

Fonte existente: branch `research/multi-asset-fusion-discovery-2026-10-26`, diretório `research/multi_asset_fusion_v01`; freeze `9273b1446977d23b4896d73d54d27d497fdc528c`. AVAX já conhecido é referência, não candidato novo.

O relatório `VERDICT_PT.md` e `source_audit.json` declaram:
- 319 pares ZIP/CHECKSUM; **319 hashes coincidem**;
- **311 arquivos com calendário completo, 8 incompletos**;
- SOL e XRP USD-M em fevereiro/2022 (26–28) e abril/2022 (1–2), diários + horários;
- **SOURCE_INCOMPLETE / FAIL_CLOSED / SEM RESULTADOS ECONÓMICOS**;
- 2024–2026 não foram abertos para resultados protegidos.

O novo `science_gate_v032.py` verifica o recibo do source audit em modo read-only e emite o estado `SOURCE_INCOMPLETE_FAIL_CLOSED`. Mesmo caso as fontes passassem, a saída continuaria `NOT_ECONOMIC_CERTIFICATION`, nunca um resultado PnL automático.

Uso:
```powershell
py science_gate_v032.py source_audit.json --output source_gate_v032.json
```

**Não alterar o protocolo original para excluir os dias incompletos, substituir moedas ou otimizar custos depois de conhecer lacunas/resultados.** Qualquer novo estudo científico exige protocolo separado. Sem trades, contas, chaves, Render, Telegram, main merge ou holdouts 2024–2026.

## Testes

16 testes locais passaram (8 inspeções sintéticas dos source-gates + 8 verificações estáticas Pine) no pacote entregue ao operador. GitHub CI e compilação Pine não foram executados nesta branch; o estudo Multi-Asset original tem 26 testes próprios no ramo separado.
