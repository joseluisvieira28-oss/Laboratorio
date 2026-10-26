"""Package evidence after replay; never changes strategy or sources."""
import hashlib,json,platform,shutil,zipfile
from pathlib import Path
import numpy as np
P=Path(__file__).parent;R=P.parent/'recovery_review';O=P/'replay-final'
sha=lambda b:hashlib.sha256(b).hexdigest()
same={n:sha((O/n).read_bytes())==sha((P/'replay-repeat'/n).read_bytes()) for n in ('report.json','daily.csv','manifest.json','provenance.json','source_gate.json')}
assert all(same.values())
(P/'reproducibility.json').write_text(json.dumps(dict(byte_identical=same,python=platform.python_version(),numpy=np.__version__,replay_exit=0,repeat_exit=0,regression_tests=26,recovery_tests=8),indent=2)+'\n')
selected=['SHA256SUMS.json','api_evidence_retry.json']
selected += [p.name for p in R.glob('api_*_2022-*.json')]
for a in ('SOLUSDT','XRPUSDT'):
 for tf in ('1d','1h'):
  for d in ('2022-02-26','2022-02-27','2022-02-28','2022-04-01','2022-04-02'):
   selected += [f'{a}-{tf}-{d}.zip',f'{a}-{tf}-{d}.zip.CHECKSUM']
with zipfile.ZipFile(P/'recovery_inputs.zip','w',zipfile.ZIP_DEFLATED) as z:
 for name in sorted(selected):
  info=zipfile.ZipInfo('recovery/'+name,date_time=(2026,10,26,0,0,0));info.compress_type=zipfile.ZIP_DEFLATED;z.writestr(info,(R/name).read_bytes())
report=json.loads((O/'report.json').read_text());basket=report['inference']['cross_asset']
lines=['# Fusion Multi-Asset V0.2 Source Recovery','',
'**Veredito: source gate PASS; replay executado; edge não certificado. Descoberta exploratória, não OOS.**','',
'Protocolo congelado no commit `9c2e9456877093ecb4f74cdd8a63aabae21de0ce`, antes de leitura/cálculo de resultados económicos desta execução. Lacunas e plano de recuperação já conhecidos: não é pré-registo independente. V0.1 preservada em `ac6e9d22328c2b91a46b7b16bfdcb9a577aa6d6d`.','',
'## Integridade e execução','',
'319/319 ZIPs mensais e CHECKSUMs coincidem com a auditoria original e foram novamente validados. Os oito meses incompletos permanecem inalterados. 20/20 ZIPs diários oficiais e CHECKSUMs recuperam apenas os 10 D1 e 240 H1 permitidos. Nenhuma observação existente foi substituída; a diferença de timestamps é exatamente a whitelist. API USD-M: 250/250 candles iguais nos primeiros 11 campos numéricos. OHLCV D1 igual à agregação H1 nos dez dias/ativo.','',
'As capturas anteriores da API foram encontradas localmente, conferidas com o manifesto SHA256 e recibos públicos de pedidos, e incluídas no pacote; não são apresentadas como novos pedidos à API. A primeira captura continha timeout em SOL H1 fevereiro; o recibo retry contém a resposta integral. Os arquivos mensais locais foram conferidos com os hashes da versão exata do GitHub. A cópia local inicial da auditoria diferia byte a byte e foi substituída apenas no diretório V0.2 pela referência exata antes do PASS.','',
'Código de saída do gate e replay: **0**. Duas execuções independentes geraram report, ledger, manifest, provenance e source_gate byte a byte idênticos. **26/26 testes de regressão e 8/8 de recuperação aprovados**. As primeiras tentativas de testes falharam por permissões de limpeza no diretório temporário do Windows; repetidos com temporários no workspace, passaram sem alteração da estratégia. Falhas iniciais e logs preservados.','',
'## Resultados por custo','',
'Cesta descritiva com peso igual nos cinco ativos, AVAX excluído. Médias por todos os 730 dias; bps aditivos, sem capitalização, não são retornos de carteira executável.','',
'| Custo roundtrip (bps) | Fusion bps/dia | Baseline bps/dia | Diferença bps/dia |','|---:|---:|---:|---:|']
for c in ('0','4','8','14','20'):
 b=basket[c];f=b['equal_weight_research_basket']['mean_bps_per_calendar_day'];delta=b['delta_bps_day'];lines.append(f'| {c} | {f:.6f} | {f-delta:.6f} | {delta:.6f} |')
lines+=['','## Ativos — cenário 14 bps','', '| Ativo | Fusion bps/dia | Baseline bps/dia | Diferença | p Holm25 |','|---|---:|---:|---:|---:|']
for a in report['inference']['asset_order']:
 v=report['results'][a]['14'];p=next(x['p_holm_25'] for x in report['inference']['tests'] if x['asset']==a and x['cost_bps']==14)
 lines.append(f"| {a} | {v['fusion']['mean_bps_per_calendar_day']:.6f} | {v['baseline']['mean_bps_per_calendar_day']:.6f} | {v['fusion_minus_baseline_bps_per_day']:.6f} | {p:.6f} |")
lines+=['','Todos os 25 testes primários, intervalos e p-valores estão em `replay-final/report.json`. A 14 bps nenhum dos cinco testes tem p Holm25 < 0,05. A 20 bps SOL e BNB têm p Holm25 < 0,05 para a diferença face ao baseline; isso é uma comparação relativa condicionada ao custo, não certificação de rentabilidade ou edge. A melhoria com custo maior decorre também da redução de operações. Nenhum cenário foi selecionado ou otimizado após os resultados.','',
'## Robustez e limitações','',
'O relatório JSON inclui todos os ativos/custos por ano e direção, remoção dos 1/3/5 maiores ganhos, correlação diária, leave-one-out, bootstrap pareado estratificado por ano L30 com 10.000 réplicas seed 271 e Holm25, preservados do código V0.1. A referência AVAX é exposta e fica fora dos 25 testes e da cesta.','',
'A 14 bps, todos os leave-one-out mantêm média Fusion negativa (entre -4,869 e -1,905 bps/dia). Correlações fora da diagonal: 0,530–0,722. Cesta Fusion: total aditivo -2157,885 bps; removendo os 1/3/5 maiores ganhos: -2637,961 / -3468,244 / -4133,625 bps. Logo, melhoria sobre baseline não equivale a rentabilidade líquida.','',
'Persistem seleção de sobreviventes, investigação prévia, ativos correlacionados, multiplicidade histórica desconhecida, revisões atuais dos arquivos e opens OHLC como proxies de execução. Os IC e p-valores seguem exatamente o método exploratório V0.1; não constituem confirmação independente. Sem holdout ou validação de fills.','',
'2024–2026 permaneceu fechado. Sem interpolação, exclusão de datas/ativos, tuning, ordens, live/paper trading, contas, APIs privadas, wallets, deploy, despesas, alteração de main, PR #271/#272 ou merge.','',
'## Evidências','',
'- `protocol.json`: contrato congelado; `run.py` e `reference_replay.py`: gate e replay.','- `replay-final/manifest.json`: 339 pares com URLs e SHA256.','- `replay-final/provenance.json`: exatamente 250 inserções; zero substituições.','- `recovery_inputs.zip`: 20 ZIPs diários, CHECKSUMs, oito corpos API e recibo retry.','- `replay-final/report.json` e `daily.csv`: resultados completos e ledger de 4380 linhas.','- `reproducibility.json`, logs de testes e `SHA256SUMS.json`: reprodução e hashes.','']
(P/'VERDICT_PT.md').write_text('\n'.join(lines),encoding='utf-8')
names=['README.md','protocol.json','run.py','reference_replay.py','reference_source_audit.json','listings.json','fetch_monthly.py','test_recovery.py','package.py','VERDICT_PT.md','reproducibility.json','recovery_inputs.zip','regression.txt','regression_workspace.txt','recovery_tests.txt','recovery_tests_workspace.txt']
names += ['replay-final/'+p.name for p in O.iterdir() if p.is_file()]
names += [d+'/'+n for d in ('gate-first','gate-second','gate-third') for n in ('source_gate.json','exit_evidence.json')]
hashes={n:sha((P/n).read_bytes()) for n in sorted(names)}
(P/'SHA256SUMS.json').write_text(json.dumps(hashes,indent=2)+'\n')
names+=['SHA256SUMS.json']
(P/'publish_names.json').write_text(json.dumps(names))
print(json.dumps({'files':len(names),'recovery_zip_bytes':(P/'recovery_inputs.zip').stat().st_size,'report_sha256':hashes['replay-final/report.json'],'ledger_sha256':hashes['replay-final/daily.csv'],'repeated_identically':same},indent=2))
