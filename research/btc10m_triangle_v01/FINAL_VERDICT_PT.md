# Crypto Lab — BTC10M triangular: veredito final de 2 de novembro de 2026

**FAIL_SAMPLE / NO-GO. Versão encerrada, sem resgate de limiares.**

## Pergunta e resultado
A discrepância persistente entre BTCUSDC × USDCUSDT e BTCUSDT antecipa a direcção de BTCUSDT nos 10 minutos seguintes?
A regra foi congelada com discrepância de pelo menos 5 pontos base nas três velas fechadas anteriores, todas com negócios e volume positivos. Não houve treino, selecção de variantes nem optimização depois dos resultados.

| Período | Sinais | Acertos | Erros | Empates | Dias | EV hipotético q70 / sinal |
|---|---:|---:|---:|---:|---:|---:|
| Abr–Dez 2023, diagnóstico | 5 | 3 | 2 | 0 | 5 | +0,02 |
| Jan–Dez 2024, OOS cronológico | 2 | 0 | 2 | 0 | 2 | -1,00 |

2024: dois sinais DOWN, ambos seguidos de subida. A perda simulada é de **2 unidades de stake**, tanto q70 como q80; não é perda real nem percentagem de uma conta. A amostra não suporta estimar com precisão a taxa de acerto ou o verdadeiro retorno esperado. O diagnóstico de 2023 com cinco casos não demonstrou vantagem.

Os critérios exigiam >=300 previsões não empatadas e >=20 dias em 2024. Foram obtidos 2 e 2. O limite inferior bootstrap q70 foi -1,00; nenhum dos quatro trimestres teve EV q70 positivo (Q1=-1, Q2=-1, Q3/Q4 sem sinais). Q80 também -1,00. Os dois testes emparelhados não sobreviveram. A classificação primária irrevogável é **FAIL_SAMPLE**, sem vender dois erros como prova de que o mecanismo inteiro é impossível. A versão é inutilizável segundo a frequência e os critérios económicos pré-fixados.

## Proveniência e sequência verificável
1. [Pré-registo 02b21b4](https://github.com/joseluisvieira28-oss/Laboratorio/commit/02b21b4a5ae9f800272685a3699119e755f81abc): antes de descarregar preços desta experiência.
2. [Código congelado b92d90e](https://github.com/joseluisvieira28-oss/Laboratorio/commit/b92d90ed50383ee9cefc0fa585d23e18ce95deb6): antes da execução.
3. [Segunda implementação 041285a](https://github.com/joseluisvieira28-oss/Laboratorio/commit/041285ab571ac4e3fe3fbd0a119199a36599321f): preparada antes de observar os resultados, sem importar funções do teste.
4. Execução local Python 3.14.6, biblioteca padrão, sem GitHub Actions, contas, serviços pagos ou ordens.
5. Recálculo separado completo dos ficheiros originais: PASS, com os sete sinais de ambos os períodos idênticos em timestamps, sentidos, preços e resultados.

Documentação da fonte: [Binance Public Data](https://github.com/binance/binance-public-data). Todos os **63 ZIPs** (21 meses × 3 símbolos) tiveram SHA256 igual ao respectivo checksum oficial, e **100% de cobertura mensal**; não houve preenchimento, substituição de fontes ou exclusão selectiva de meses. Os URL exactos, hashes e contagens estão em source_manifest.json e source_quality.json. Os bytes descarregados ficam conservados localmente em raw/. Não são incluídos no Git por dimensão; uma futura revisão do fornecedor pode mudar os arquivos, pelo que o manifesto fixa os hashes desta execução.

## Auditoria: PASS de reprodução, âmbito explícito
audit_replay.py relê os 63 ZIPs, verifica novamente os hashes, faz junção por timestamp em dicionários em vez das matrizes do teste e decompõe os logaritmos para uma construção separada do residual. Reproduziu todos os sete eventos e os payoffs com aritmética inteira em décimos de stake. Um segundo bootstrap com semente diferente confirmou os limites negativos. O teste sintético de causalidade alterou preços em B e no futuro sem alterar o sinal B.

**É uma auditoria computacional por implementação separada, executada pelo mesmo agente. Não é revisão externa por investigador independente.** A independência externa solicitada não foi satisfeita; não se apresenta esse requisito como PASS. A reprodução confirma o resultado da regra e a origem dos dados, não uma vantagem negociável. Ver audit.json.

## Limitações materiais
- São fechos de velas, não cotações simultâneas ou bid/ask executáveis. Diferenças de última transacção e liquidez podem gerar um residual sem oportunidade económica.
- OPEN(B) é uma referência idealizada posterior às velas usadas, mas pode anteceder a disponibilização efectiva de todas as velas. Latência e execução humana não foram provadas.
- q70/q80 são cenários simbólicos, não payouts históricos MEXC. Não houve paridade de índice de liquidação ou de produto.
- 2024 é OOS cronológico da regra, mas **não um holdout global virgem** do laboratório. A pesquisa anterior já o observou.
- A novidade foi delimitada por inventário dos 1086 ramos e leitura do protocolo anterior de peg USDCUSDT. Não se reivindica revisão integral de todos os ramos nem novidade universal.

## Decisão vinculativa e estado anterior
Encerrar BTC10M_TRIANGULAR_NUMERAIRE_001. Não reduzir 5bp, encurtar persistência, inverter sentido, seleccionar meses ou abrir 2025 para salvar esta versão.
LOGIT_P60 mantém o seu fecho anterior: 1185 sinais de 2024, 55,79% nos não empatados, q70 negativo e q80 não robusto; não foi retreinado nem reavaliado. [Relatório anterior](https://github.com/joseluisvieira28-oss/Laboratorio/blob/73fc353385e5c42c2363b0bccbd768ecc81f9bc0/research/btc10m_behavioural_v01/BTC10M_BEHAVIOURAL_2023_SELECTED_2024_OOS_FINAL_ECONOMIC_CLOSEOUT_2026_11_01.md).

**Nenhuma vantagem económica certificada. Sem trading, contas, ordens, compras, alertas, deploy ou merge. Nenhum preço de 2025/2026 foi aberto.**
main permaneceu em 75fb36c8337c3221b7551c513e049cd472dad231, o mesmo pai do pré-registo. Todo o trabalho está num ramo de investigação separado.
A API indicou private=false no repositório; a visibilidade não foi alterada. Os artefactos publicados contêm apenas investigação e dados públicos.

## Hashes SHA256 dos recibos
- results.json: 3ed6c2630fab0a39e855e8a0493f02dfe3f3f31ce9e3cc166c7b3774c7898f7b
- source_manifest.json: 3a10cef977fd1ba76605c0507791f68fe82f0ae70a59be1dd2e0a2a1d467c4f3
- source_quality.json: 74a9fd4721274f5e25d045b1b5cb9d4098d71a3d72aed1564ebdf3cfa90739f4
- events.json: c36407693d686279d6e0bbcd004df2fb51fcc9c36d2da5db08eaced0d094a153
