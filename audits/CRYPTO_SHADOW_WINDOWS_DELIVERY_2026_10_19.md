# Entrega operacional Crypto Lab — 19 outubro 2026

**Veredito: NO-GO para dinheiro real. Operador de recolha pública funcional; máquina de lucro comprovado: não.**

CONVEX V07 (#251) terminou com zero sobreviventes aos critérios de robustez; Funding Hunter V04 (#256) teve 28/28 decisões FLAT na configuração congelada. Nenhum destes resultados demonstra edge líquido independente. O resultado Funding é específico da amostra/regra, não prova inexistência de qualquer edge no mercado.

Antes de programar foram inspecionados o cliente MEXC, o coletor `MEXCDataCollector`, o leitor V07/V11/V12 de outbox e o gate de custódia já existentes. Esta entrega reutiliza o cliente/transport e copia sem alterações o leitor e gate, com Git blob hashes verificados. Não cria outro motor de indicadores nem altera parâmetros das estratégias. A base futures MEXC usada neste operador é a atual `api.mexc.com`; o comportamento dos restantes consumidores do cliente permanece igual quando não configuram o callback opcional de arquivo.

## Entrega e smoke real

Pasta portátil Windows de aproximadamente 10,2 MB comprimida, incluindo executável e dependências Python. Extrair e correr `Smoke.cmd` ou `Run.cmd`. Painel `state/painel.html`, JSON por dia UTC, bytes públicos arquivados por SHA256 e cadeia SQLite verificável offline. Observação de futures MEXC SOL/BNB e OKX BTC linear/inverse, sem endpoints históricos ou privados. Recolha contínua apenas enquanto o operador estiver aberto; não foi instalado serviço ou tarefa agendada.

O ZIP final foi extraído numa **pasta com espaços, fora do repositório**, e o executável completou o smoke público e a verificação offline. **15 respostas HTTP públicas**, 1 snapshot e 1 falha de outbox ausente. SOL MEXC BID/ASK **105,17 / 105,18 USDT**; BNB **728,2 / 728,3 USDT** à hora do recibo, não cotações atuais garantidas. Ambos os conjuntos de endpoints atuais OKX responderam nesse ciclo. Uma primeira sonda direta OKX tinha devolvido 403; a recolha pelo transport existente com os seus headers funcionou posteriormente. Não foi usado fallback de corretora.

Recibo sanitizado: [SMOKE_RECEIPT_2026-10-19.json](../tools/crypto_shadow/SMOKE_RECEIPT_2026-10-19.json). Contém timestamps, hashes, limites e contagens. Dados brutos ficam locais. Não há ordem, fill, cashflow de conta ou PnL. O líquido em USDT/EUR é desconhecido, não zero inventado.

## Verificação e limites

- **11/11 testes específicos passaram no Windows**, incluindo bytes HTTP, adulteração, restrição de endpoints, profundidade e unidades de contrato, NaN/preços inválidos, duplicados, outbox de teste e funding sintético separado dos resultados reais.
- Suíte existente executada da pasta correta: **35/38 passaram**; três erros de `test_gate_f_recovery` em `gate_f_replace.fsync_directory`, por `os.open` de diretório em Windows. Estes ficheiros estão inalterados. Uma primeira execução da pasta errada também causou três falhas de caminhos em compaction, eliminadas ao corrigir a pasta de execução. Não se declara suíte completa PASS.
- O executável final e os recibos passaram a verificação de integridade. O workflow do draft repete os testes offline em Windows/Linux e produz pacote Windows; o resultado CI deve ser consultado no PR, sem o antecipar neste relatório.
- **Nenhum sinal de estratégia autêntico foi observado neste ambiente**: V07 outbox não encontrado. A instalação existente do utilizador não foi alterada. O leitor está pronto a observar novos IDs nas duas lanes originais, mas os outboxes existentes não oferecem hashes de fonte/warmup; alertas ficam sem certificação, não são contados como amostras independentes.
- Nenhum settlement futuro, decisão real das 00:05, saída de 24h ou teste prolongado foi concluído hoje. O registo de settlements só admite timestamps posteriores à instalação; os dados têm de estar testemunhados antes das 00:05 para a decisão desse dia. A taxa prevista nunca substitui a realizada.
- Capturas REST a cada 30s não demonstram continuidade, execução de stops ou ausência de oportunidades entre capturas. Custos de conta, FX, funding em moeda correta, marcas, gaps, stops e saídas precisam de certificação. A cadeia local não é testemunho independente.

Não foram usadas chaves, contas privadas, wallets, ordens, capital, recursos pagos ou ficheiros históricos de holdout 2026. Só novas observações públicas atuais autorizadas. `main` não foi alterada nem fundida. O ZIP não inicia o operador por si: o utilizador extrai e executa.

## Próximo resultado económico concreto

A prioridade técnica seguinte é ligar provas de fonte ao **observador original**, não criar novos indicadores nem preencher artificialmente os campos que faltam. Até lá, o painel serve para observar cotações e bloqueios com recibos. A amostra independente exigida pelo gate não pode ser antecipada por software.

Como via de receitas de curto prazo independente do mercado: propor um piloto pago de reconciliação de stocks/relatórios Excel para pequenas empresas da rede do utilizador. Demonstração em 48h, oferta de âmbito fixo, preço piloto **proposto** de 150–300 EUR, cinco contactos apenas com autorização e entrega numa semana. É uma proposta comercial por validar, não previsão de vendas. Nenhuma mensagem foi enviada. Instruções e limites em [README_PT.md](../tools/crypto_shadow/README_PT.md).
