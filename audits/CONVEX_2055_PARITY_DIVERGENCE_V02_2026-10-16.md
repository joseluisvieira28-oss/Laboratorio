# CONVEX 20:55 — Divergência de paridade SOL V07↔V12, follow-up forense V02

**Base:** JSON sanitizado fornecido pelo operador após executar o verificador `CONVEX_2055_TWO_SIGNALS_OFFLINE_READONLY_V01` no próprio Windows. Sem acesso local direto do investigador e sem upload de bases SQLite/caches.

## V07 SOL 5m (2026-10-15T20:55:00Z)
- `pinned_v5_replay_five_minute_signal=true`; janela V07 reconstruída com **12,576/12,576** velas; `overlap_conflicts=0`; `window_sha256=51700685354249a40c276a5e7b3f74d14a429461a48f27361495c679ff38a0f5`.
- Linha SQLite exata encontrada; binding de ID e símbolo verdadeiros; `db_marked_sent=true`; timestamp guardado `2026-10-15T20:55:11.569Z`; `telegram_message_id=222`.
- Segunda janela V12 SOL também reconstruída, hash `f779d117a426cb6d76275b49fdf63585d2ae718e4b55b48533c17d82a26ead4e`. **Hashes diferem**, embora cada monitor, internamente, não reporte conflitos entre backup e cache atual.
- Resultado SOL: **paridade entre observadores falhou**. Isto não anula replay positivo V07 nem prova sinal inválido; impõe localização da(s) divergência(s), especial atenção ao último candle e ao efeito do RSI/Wilder e SMA200.

## V12 BNB 5m
- `pinned_v5_replay_five_minute_signal=true`; 12,576/12,576 velas; fonte V12 hash `887c39816e424b1e940d3eb996d74fcc3461cbba1685ecc7976ac310d1ae35b7` coincide com fonte V07 BNB.
- Linha SQLite exata encontrada e marcada enviada, `sent_at_utc=2026-10-15T20:55:35.766Z`; `close_matches_image=true`. A versão V12 não guarda Telegram API `message_id`; falta receipt numérico vinculado à linha.
- Resultado BNB: `LOCAL_CAUSAL_REPLAY_PASS_NOT_EXTERNAL_MARKET_PARITY`. É paridade entre duas janelas locais, **não** validação externa independente do fornecedor nem rentabilidade.

## Instrumento de diagnóstico V02 (offline somente)
- Extende o verificador anterior com `cross_observer_diagnostic`: número exato de candles divergentes; primeira/última hora UTC de abertura; `open/high/low/close/volume` por contagens sem valores numéricos; diferença na última vela (20:50 UTC); número de diferenças nas 20 e 200 últimas velas; e executa V5 também sobre a cópia independente.
- Instrumentação adicional tem testes sintéticos para divergências históricas sem conflito interno e para divergência na última vela. Não modifica fonte V5, estratégia, critérios económicos, outboxes, Telegram ou Windows tasks.
- Não presumir que diferença é devido a erro de Binance, relógio, arredondamento, repainting ou mistura de snapshots até localizar pelo novo diagnóstico.

## Decisão
- Telegram receção: observação visual positiva das duas mensagens anteriores, persistência local confirmada das duas linhas.
- SOL: **SOURCE_PARITY_BLOCKED**, causa ainda não atribuída. BNB: **LOCAL_CAUSAL_SOURCE_PARITY_PASS**, paridade externa não provada.
- **NENHUMA AUTORIZAÇÃO PARA REAL MONEY, SL/TP, 10×, ordens, merge main ou post-outcome tuning** a partir desta evidência.

Próximo receipt: executar somente V02 no Windows, verificar SHA256 e partilhar JSON sanitizado. Se as diferenças envolverem a vela do próprio sinal, investigar prioridade máxima; se forem antigas, quantificar dependência da RSI e avaliar o replay de ambas versões.
## Receipt V02 concreto recebido do operador — 16/10/2026

O operador executou o verificador read-only V02 no Windows e entregou este resumo, **sem publicar OHLC**:

| Medida | SOL V07 vs V12 | BNB V12 vs V07 |
|---|---:|---:|
| Candles comparados | 12.576 | 12.576 |
| Candles diferentes | **3** | **0** |
| Opens/highs/lows diferentes | 0/0/0 | 0 |
| Closes diferentes | 3 | 0 |
| Volumes diferentes | 3 | 0 |
| Primeira divergência SOL | 2026-10-15 14:45 UTC | — |
| Última divergência SOL | 2026-10-15 19:50 UTC | — |
| Divergências últimas 20 barras | 1 | 0 |
| Divergências últimas 200 barras | 3 | 0 |
| Vela do sinal (open 20:50 UTC) | idêntica | idêntica |
| Flag pinned V5 ao close 20:55 | true / true | true / true |
| Paridade completa V07-V12 | **false** | **true** |

O facto de duas janelas locais SOL gerarem o mesmo flag V5 é prova de **robustez da decisão específica perante as diferenças verificadas**, mas não de autenticação externa do preço, nem demonstra que as diferenças de close/volume não alterariam outros sinais ou o estado de uma posição. A divergência de uma barra nos últimos 20 candles pode afetar SMA20, BB20 e volume SMA20 do signal close; o Wilder RSI também depende do histórico anterior. A janela de 12.576 barras contém os mesmos timestamps, mas isso por si não identifica quais candles foram originalmente publicados por Binance.

### Hipóteses de causa — todas NÃO TESTADAS

1. Dados públicos revistos/alterados entre instantes em que as duas aplicações criaram os caches.
2. Snapshots lidos em momentos diferentes, algum snapshot com volume e close ainda atualizados apesar do timestamp de candle fechado.
3. Serialização/precisão numérica diferente ou transformação na fonte.
4. Cache histórico recuperado por fontes REST iguais mas com valores alterados no backend do fornecedor.

**NÃO afirmar manipulação ou adulteração intencional**; os dados não justificam essa inferência.

### Nova verificação V03

O novo CLI V03 imprime **apenas** as três horas UTC exatas de candle divergente, magnitude relativa dos deltas close/volume, e a pontuação e flags booleanas do V5 em ambas as fontes. Estes diagnósticos não mudam estratégia, vela de sinal, trade entry, stop, nem TP, e não abrem o holdout 2026. Sem execução no Windows ainda, não declarar causa resolvida.

**GO científico limitado: BNB local replay+parity; SOL sinal verdadeiro nas duas janelas mas paridade integral BLOQUEADA; trading/economic GO = NÃO.**
