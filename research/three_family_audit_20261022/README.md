# Auditoria de três famílias — 2026-10-22
**Próximo veredito defensável atingido: nenhuma promoção.** Research only; main preservada; sem ordens, wallets, chamadas privadas, alertas ou deployment.

|família|veredito separado|trabalho desta auditoria|
|---|---|---|
|Token Unlock Supply Shock|manter NO_EDGE do MVE exato|duplicado encontrado;237 eventos/77episódios verificados aritmeticamente;nenhum OOS de resgate|
|Funding Crowding|manter NO_PROMOTION da família PCU e falha DCV|BTC/ETH/SOL/BNB já estudados;custos de funding omitidos e timing de entrada não demonstrado no PCU|
|DCA Adaptativo|superioridade histórica não replicada;edge independente inconclusivo|regra congelada,replay único2021–25,2anos temporais OOS,cenários15/30bps por lado|

Ler TOKEN_UNLOCK_VERDICT.md, FUNDING_CROWDING_VERDICT.md e ADAPTIVE_DCA_VERDICT.md. As conclusões são restritas às especificações testadas; não rejeitam universalmente as famílias.
São adjudicações separadas feitas nesta sessão, não peer review por investigadores externos.

## Integridade e sequência
- Base main:75fb36c8337c3221b7551c513e049cd472dad231.
- Branch de trabalho:research/unlock-crowding-adaptive-dca-audit-2026-10-22.
- Pré-registo antes dos novos outcomes:1d746cd94451829d5b70402f0f70fbee8f761421.
- Implementação inicial:0ce22ccc50438ff2fea58df34180119b144daf14.
- Correção técnica antes de outcomes:4bcbad3e6644cea2b297837e86959915bcd86094;zero balance antes do primeiro depósito.
- Gate fonte+testes persistido antes de outcomes:212048b8531929c74f205d8cd514ceb9c46957f6.
- SOURCE_PASS inicial11:47:54UTC;único replay outcomes11:48:58UTC.
-2353 verificações contabilísticas independentes do ledger:PASS.
- Sem parâmetro económico alterado após outcomes. Os estudos anteriores já tinham outcomes conhecidos antes do freeze novo; estão claramente identificados como auditoria retrospectiva.

## Fontes, ficheiros e reprodução
INVENTORY.json regista1023branches em11páginas+12ªvazia e as correspondências relevantes. Não é censo de todos os blobs de todas as branches; novidade DCA é limitada a esse inventário.
SOURCE_MANIFEST_PRE_OUTCOMES.json conserva URLs,bytes,hashes,timestamps da aquisição;SOURCE_MANIFEST.json é a posterior revalidação dos mesmos bytes. SOURCE_PASS_BEFORE_OUTCOMES.json é o recibo imutável do gate. Ler SOURCE_GATE.json e ACCOUNTING_VERIFICATION.json.
DCA_RESULTS.json contém40cenários anuais fixos (5anos×2custos×4regras);não são40hipóteses selecionadas. DCA_LEDGERS.csv contém todas as compras,caixa,unidades e fricção. dca_replay.py reproduz os resultados;verify_accounting.py verifica o JSON de ledgers que o replay gera.
Só Python standard library. Executar dca_replay.py --test para sintéticos; --source-only para adquirir/verificar sem outcomes; sem flag para replay autorizado por este freeze. Não abrir2026. Para reprodução offline,colocar os72ZIPs e72sidecars emraw/.
Foram adquiridos163309bytes de arquivos+sidecars,custo monetário adicional0. Pacote local conserva também raw/. Nenhuma chave de exchange/API é necessária.

## Obstáculos reais e limites
DNS local falhou inicialmente;INITIAL_DNS_FAILURE.json preservam a falha. A execução com permissão de rede resolveu a aquisição. Não é blocker atual.
Alguns endpoints do conector rejeitam slash percent-encoded em refs; leituras por SHA imutável funcionaram. Nenhum fallback para serviços privados.
Token Unlock não reexecutado desde fontes upstream;Funding não reexecutado desde raw. Auditoria de relatórios/código+aritmética não é replicação integral.
Em Funding falta funding cashflow e não se prova known_at antes do open de entrada. No DCA faltam preço executável/latência,independência estatística de dois anos e confirmação prospectiva. Custos de15/30bps são cenários;taxas,USDT/contraparte/impostos não demonstrados.
Não há ação futura agendada,nem coleta contínua,ordens ou promoção implícita. O estudo termina neste veredito;qualquer nova regra exige nova hipótese e freeze prospectivo.
