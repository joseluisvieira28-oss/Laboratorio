# Economic Proof Engine V1 — investigação offline

**NO-GO LIVE.** Um ledger verificável não demonstra vantagem. Este módulo não tem
cliente de exchange, ordens, credenciais, dependências externas nem workflows.
Foi acrescentado numa branch isolada sobre o snapshot Deribit V2
`7a7d58336f68ea483e00a3c7623c4e5777263da5`; os coletores, arquivos e freeze herdados
permanecem intactos. Ver [auditoria dos quatro gates](AUDIT_2026-11-05.md).

## O que permite

- Precommit de sinal e abstenção, estratégia, fase, cohort, versão das regras,
  informação disponível, deadline de entrada e risco definido antes da entrada.
- Eventos de entrada/saída por instrumento e perna, quantidade, preço e cash flow;
  custos assinados de taxas, funding, delivery, liquidação, empréstimo,
  transferência, conversão e outros custos.
- PnL líquido, R-multiple, média por trade, taxa de acerto, profit factor,
  pior R observado e drawdown realizado na moeda única do estudo.
- Separação por estratégia, hash de regras e fase; abstenções elegíveis mantidas
  como zero por cohort; incompletos identificados e excluídos de inferência.
- Intervalo exploratório por moving-block bootstrap de cohorts: bloco 7,
  10 000 réplicas, seed 20261105; sem intervalo abaixo de 30 cohorts ou quatro
  blocos. Estes defaults NÃO substituem o desenho congelado de cada estratégia.
- Hash chain, ligação de todos os eventos ao precommit, IDs únicos, datas
  conscientes de timezone e rejeição de NaN, moedas misturadas ou custos desconhecidos.

## Contrato contabilístico

Valores monetários são strings decimais (não floats JSON) numa única moeda.
`cash` nas entradas/saídas é o fluxo económico do instrumento **antes das taxas
separadas**. Um adaptador auditado é responsável pela fórmula do produto.
Exemplo linear: compra de 1 a 100 -> -100; venda a 110 -> +110. Para perpétuos,
inverse, conversões, expiries e outros multiplicadores não usar automaticamente
essa fórmula: o adaptador deve preservar as fontes e produzir o cash flow correto.

`net = soma(cash das entradas/saídas) + soma(cash dos custos)`.
Custos negativos debitam; rebates e funding recebido são positivos.
`R = net / risco precommit`, sem recalcular o risco depois da perda.
Spread e slippage são decomposições assinadas já embutidas nos preços/cash flows;
**não são descontados novamente**. Em expiry, não inventar uma venda ao bid nem
uma segunda cobrança de spread. Uma liquidação total incluindo trading fee
deve ser decomposta em custos incrementais para não duplicar a taxa normal.

Fecho exige entrada e saída de todas as pernas, reconciliação explícita e cobertura
de todas as categorias de custo como `recorded` ou `not_applicable`. Um custo
conhecido zero usa evento `cost` com cash `0`. `not_applicable` é uma afirmação de
escopo sustentada pela evidência de reconciliação, nunca substitui um custo
desconhecido. Funding/rede/FX desconhecidos impedem uma alegação pessoal all-in;
um estudo apenas de venue não pode ser promovido a retorno pessoal all-in.
Taxas fiscais específicas, se incluídas no escopo, precisam de registo em `other`.

Os campos de quantidade/preço e a lista de pernas reconciliadas ajudam a revisão;
V1 **não comprova sozinho posição flat, fórmula do produto ou autenticidade de
fills**. Não está ligado ao collector e não produz entradas Deribit artificiais.
Um adaptador por produto e a verificação das fontes continuam obrigatórios.

## Precommit e integridade

Cada linha JSONL contém `previous`, `event` e SHA256 canónico em `hash`.
Evento inicial: `kind=precommit`, `decision=enter|abstain`, `phase`, `strategy`,
`rules_sha256`, `cohort`, `currency`, `risk`, `information_cutoff`, `entry_deadline`,
`at`, `id`, `trade_id`, `evidence_sha256`, `simulation=true`.
Eventos seguintes têm `commitment` igual ao hash da linha do precommit;
também têm identidade, timestamp, moeda e hash da evidência.
Entradas/saídas têm `instrument`, `leg`, `side`, `quantity`, `price`, `cash`,
`spread_embedded`, `slippage_embedded`; custos têm `category`, `cash`;
fecho tem `coverage`, `reconciled_legs`, `reconciliation_evidence`.

Publicar e reter externamente o head **antes da entrada**: um hash e um relógio
local não provam precommit independente. `--expected-head` deteta truncagem ou
reescrita relativamente à âncora fornecida; uma cadeia totalmente reescrita sem
âncora é indistinguível. O histórico Git também exige retenção fora de uma branch
que possa ser reescrita. Nunca guardar dados privados no repositório público.

Append usa um lock exclusivo lateral e valida antes de escrever. É single-writer,
com fsync, sem recuperação automática de crash. Lock abandonado ou última linha
incompleta requer inspeção; não apagar ou reconstruir silenciosamente.

## Reprodução sem mercado

Da raiz do repositório, com Python 3.11+ e biblioteca padrão:

```sh
python research/economic_proof_v1/run_checks.py
python research/economic_proof_v1/audit_deribit.py --out /novo/local/deribit-audit.json
python research/economic_proof_v1/engine.py research/economic_proof_v1/SYNTHETIC_LEDGER.jsonl
python research/economic_proof_v1/engine.py /novo/local/ledger.jsonl --append-event /local/evento.json
python research/economic_proof_v1/engine.py /local/ledger.jsonl --expected-head SHA256_RETIDO
```

`audit_deribit.py` cria um ficheiro novo, não sobrepõe o anterior. Os testes
negam conexões socket e usam uma pasta temporária local. Exemplos SYNTHETIC são
apenas dados fabricados para conferir a contabilidade, não trades nem lucro.
O exemplo: 10 de gross cash PnL, -2 de taxas, +0.5 de funding -> net 8.5,
R 0.85; 2 de spread e 1 de slippage já embutidos não são subtraídos novamente.

## Limites de inferência e execução

Fornecer TODOS os cohorts consecutivos do protocolo, incluindo zeros elegíveis,
e identificar separadamente missing/source blocked. Multiplicar sinais do mesmo
dia não cria amostras independentes. O bootstrap agrupa por cohort mas não valida
a escolha do cohort, calendário completo, multiplicidade ou estacionariedade.
O drawdown é de cash realizado no fecho; não é mark-to-market nem estima risco
intratrade, exposição simultânea, margem, insolvência ou cauda não observada.
Profit factor sem perdas é null, não uma prova de lucro infinito.

Para Deribit V2 continuam obrigatórios exatamente os gates de `FREEZE.md`:
20 elegíveis desenvolvimento +20 confirmação; OOS >=120 elegíveis, >=60 P1,
>=180 dias e >=6 meses, bootstrap seed20261102 com comparação pareada P1-C0,
stress, consistência mensal e DD <=20 risk units. Este motor genérico não calcula
nem certifica automaticamente esses gates. Não há botão ou caminho de live GO.
