# META-DIAMANTE-001

[Draft PR #409](https://github.com/joseluisvieira28-oss/Laboratorio/pull/409) · [Freeze 0b6c6f8](https://github.com/joseluisvieira28-oss/Laboratorio/commit/0b6c6f83426a280fe09e0a39fadc7a4deb395adc) · [adenda forense 48c561f](https://github.com/joseluisvieira28-oss/Laboratorio/commit/48c561fb11142abdbfb973816164b587a2cb039f). Ler REPORT.md e EXECUTIVO.md. Evidência integral em evidence.zip. ZIP do Drive inclui também scripts e documentação. Somente simulação local, sem adaptador de ordens.

## Reproduzir

Usar Python e versões em requirements.txt, git e curl. Executar os comandos nesta pasta. O resultado da verificação do histórico original requer o JSON arquivado prior_asymmetry.json que acompanha evidence.zip.

```sh
unzip -o evidence.zip
mkdir -p out legacy legacy_native
git clone --filter=blob:none --no-checkout https://github.com/joseluisvieira28-oss/Laboratorio upstream
git -C upstream fetch --depth=1 origin refs/pull/251/head refs/heads/research/convex-8alt-5m-common-2023-25-2026-10-13
paths="research/btc_convex_multifront_v01 research/btc_convex_timeframe_matrix_20261013 research/convex_8alt_common_2023_25 research/convex_multialt_4tf_20261013 labs/btc-convex-trend-capture-001/prospective_shadow_snapshot_v0_2_aggressive.py"
git -C upstream archive f3e22ce065796bc073096892599669f7df13d141 $paths | tar -x -C legacy
git -C upstream archive af82deefd5634a77a7b49e7acec61ca21eb44a49 $paths research/convex_8alt_5m_common_20261013 | tar -x -C legacy_native
python data.py
python experiment.py
python evaluate.py
python sensitivity.py
python legacy_replay.py legacy BTC SOL BNB ETH DOGE
python native.py legacy_native
python forensics.py
python verify.py
```

Não executar os runners históricos irrestritos de PR81. O download desta operação termina em dezembro de 2025. Os scripts atuais de mercado instrument.py e shadow.py são separados do replay histórico. A regeneração pode produzir timestamps diferentes nos invólucros gzip; comparar os CSV descomprimidos. Não voltar a congelar forward_model.json durante o acompanhamento.

## Dados e auditoria

out/sources.csv inventaria os 180 ficheiros spot e os hashes verificados. out/legacy contém fontes, manifests oficiais, modelos e ledgers por cenário. out/original_entries.csv liga entradas históricas de perpétuos aos regimes. out/opportunities.csv.gz enumera sinais candidatos, inclusive sobrepostos, com retornos isolados hipotéticos para treino. out/decisions.csv.gz regista seleção/rejeição na base de 10 000. out/trades.csv é o ledger BASE de 10 000. Restantes magnitudes são reproduzíveis por cenário a partir de experiment.py. out/metrics.csv abrange todos os capitais, cenários, ativos e anos. out/equity.csv.gz contém marcas diárias para cada sistema e cenário a 10 000. Colunas de score são a soma dos cinco indicadores. As probabilidades não foram estimadas. As previsões do modelo são retornos condicionais, sem alegação de calibração.

## Continuidade

Ativação verificada em forward/ por fotografia pública dos três livros. shadow.py YYYY-MM-DD aceita apenas dias completos desde 28/11/2026, ignora horas anteriores às 13:00 UTC desse dia e verifica cobertura. A fonte é recuperável posteriormente, enquanto os snapshots de livro em tempo real são irrecuperáveis por este coletor. future_score.py usa exclusivamente a coorte futura e forward_model.json; marca as posições abertas como provisórias. Pontuação a partir de 01/01/2027. Primeiro fecho anual 01/01/2028 UTC. Exigir também 100 operações fechadas do candidato e comparador e os critérios do protocolo. Sem atualização dos parâmetros, sem somar anos independentes como se fossem capital composto. A recolha recorrente própria não foi instalada devido ao limite de cinco tarefas ativas. Nenhuma tarefa existente foi alterada. Uma cotação corrente não é um par de fills histórico ou prospetivo.
