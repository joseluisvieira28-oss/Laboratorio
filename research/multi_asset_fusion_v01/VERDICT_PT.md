# Multi-Asset Fusion Radar — veredito científico, 26/10/2026

**SOURCE_INCOMPLETE / FAIL_CLOSED / ECONOMIA NÃO TESTADA / SEM LIVE GO.**

O pacote foi implementado e os dados públicos foram obtidos. A experiência
económica foi bloqueada pelas regras congeladas: os próprios arquivos oficiais
contêm lacunas. Não foi produzida classificação de moedas, rentabilidade,
correlação de retornos, significância ou recomendação de trading.

## Evidência concreta

- Protocolo congelado no GitHub antes dos candles/resultados dos candidatos:
  `9273b1446977d23b4896d73d54d27d497fdc528c`.
- Origem exata: `d4e7c542ebc67ec037ab2a1e86c8eaa07a9d8c96`, no ramo do PR #271.
  Esse ramo avançou depois; a origem da experiência não foi alterada.
- Cinco candidatos fixos: SOLUSDT, ETHUSDT, BNBUSDT, XRPUSDT, LINKUSDT.
  AVAXUSDT é apenas referência exposta; não entra na inferência dos candidatos.
- 319 pares ZIP/CHECKSUM obtidos: 25 BTC Spot diários + 6 × (25 diários USD-M
  + 24 horários USD-M). Warmup dezembro/2021; Discovery 2022–2023.
- **319/319 SHA256 coincidem com os CHECKSUM associados. 311/319 arquivos
  passaram o calendário completo. Oito falharam por candles ausentes.**
- Primeira tentativa: timeout transitório no pedido BNBUSDT H1 agosto/2022.
  A repetição resolveu o acesso, mas revelou as lacunas de calendário abaixo.
  Ambos os recibos foram preservados. Não houve fallback de fonte ou período.
- O auditor percorreu todos os 319 arquivos, sem calcular retornos. Os hashes
  de ZIP e CHECKSUM e cada timestamp ausente estão em `source_audit.json`.

| Ativo | Mês | Diários presentes/esperados | H1 presentes/esperados | Dias UTC inteiros ausentes |
|---|---|---:|---:|---|
| SOLUSDT | 2022-02 | 25/28 | 600/672 | 26, 27 e 28 fevereiro |
| SOLUSDT | 2022-04 | 28/30 | 672/720 | 1 e 2 abril |
| XRPUSDT | 2022-02 | 25/28 | 600/672 | 26, 27 e 28 fevereiro |
| XRPUSDT | 2022-04 | 28/30 | 672/720 | 1 e 2 abril |

São dez candles diários e 240 candles H1 em falta, somando os dois ativos.
Exemplo verificável: ZIP SOLUSDT diário fevereiro/2022 SHA256
`da808ec7a636e7010b47079c4565cdc9640f9b7f4f4314b785f135a10551184b`.
O CHECKSUM coincide, mas o CSV só contém 25 dias. Integridade do ficheiro
não equivale a completude do histórico. Estas ausências também afetam sinais
futuros quando D-1 ou D-21 coincide com uma data em falta.

ETH, BNB, LINK, BTC Spot e a referência AVAX passaram os respetivos arquivos
de calendário. Não executei resultados económicos nesses subconjuntos: isso
alteraria a experiência conjunta depois de conhecer a falha dos dados.

## Contratos, datas e causalidade

As fontes primárias em `listings.json` confirmam contratos USD-M anteriores
ao warmup: SOL 14/09/2020 07:00 UTC; BNB 10/02/2020 08:00 UTC;
LINK 17/01/2020 08:00 UTC; XRP já lançado em 06/01/2020;
ETH já lançado em novembro/2019; AVAX aberto em 23/09/2020.
ETH tem divergência entre a data de um blog oficial (28/11) e o anúncio
oficial (29/11); não afirmamos hora nem dia exato além dessa incerteza.
XRP e AVAX também têm apenas precisão diária nas fontes revistas.
Isto não cria ambiguidade sobre serem anteriores a dezembro/2021.
Listing não prova disponibilidade para uma conta/região, nem uptime contínuo.

O programa fixa fechos D-1 e D-21; o último termina em D 00:00 UTC menos
1 ms. A decisão usa esses fechos, entrada proxy open D 01:00, saída proxy
open D 02:00. Não usa o fecho de D. Publicação/revisão de arquivos e preços
executáveis nessas datas continuam não atestados.

## Testes e limites

26 testes locais passaram, incluindo uma cadeia sintética completa de 319
pares e 4.380 linhas, segundo cálculo Decimal, adulteração de gross/total/hash,
ausências, duplicados, OHLC inválido, clocks, holdout, sinais causais,
custos e diagnósticos de lacunas. `tests.txt` contém a saída.
O replay real falha antes de `daily.csv`/`report.json`; `exit_evidence.json`
regista o código de saída nativo. Não há alegação de CI remoto ou replay
económico autenticado PASS. O segundo cálculo Decimal passou em fixtures;
não correu sobre um ledger real porque esse ledger não foi legitimamente criado.

Os módulos de ano, direção, ativo, concentração (retirar maiores 1/3/5
ganhos), correlação por calendário, leave-one-asset-out e bootstrap pareado
estão implementados. A grelha fixa é 0/4/8/14/20 bps ida+volta, sem otimização.
Bootstrap L30, 10.000 réplicas, seed271 e Holm25 foram predefinidos, mas
**não executados sobre resultados reais** por falha do gate.

A seleção de moedas sobreviventes e familiares em 2026 não representa todo
o universo de 2022. Há seleção/sobrevivência, pesquisas anteriores e dependência
entre moedas que o Holm25 não elimina. Mesmo uma comparação positiva de
Discovery seria exploratória. Melhoria relativa pode ser apenas evitar
comissões de uma baseline perdedora; não demonstra lucro executável.

**Decisão:** não há evidência válida nesta experiência para dizer que o filtro
se generaliza aos cinco ativos, nem para concluir que falhou economicamente.
Foi a fonte que falhou o requisito de completude. Não foram interpolados dados,
removidas datas, trocados ativos ou relaxado o gate. Não foi aberto 2024–2026,
reativada estratégia, colocado trade, usado conta/chave, feito deploy, despesa
nova ou merge main. Uma eventual mudança de fonte/gate exige um protocolo
separado antes de novos resultados; não constitui autorização para o fazer.
