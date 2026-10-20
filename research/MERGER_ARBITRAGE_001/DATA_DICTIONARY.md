# Dados e relógios
Os seis casos são uma auditoria de disponibilidade, não a amostra confirmatória. Nenhum ficheiro constitui histórico de trading.
- ex_ante.csv: apenas termos de fontes originais de anúncio. Nem a lista de atualizações entre anúncio e t0 nem o calendário de negociação foram certificados; known_at_t0_certified é NO. Não usar estas linhas como features finais.
- outcomes.csv: factos conhecidos depois; nunca juntar ao processo de seleção ex-ante. Datas legais, datas de notícia, settlement previsto e recebimento real são conceitos diferentes.
- prices.csv: seis linhas de lacunas, zero observações de mercado autenticadas. NA é desconhecido, nunca zero nem sucesso.
- exclusions.csv: exclusões científicas e motivo. Spirit continua na auditoria adversarial, mas contraprestação dependente do prazo viola o universo de preço fixo v1.
- sources.csv: URLs, data de publicação quando capturada, papel e data de consulta. Os horários não capturados permanecem desconhecidos. A data de consulta não é data de conhecimento histórico.
- synthetic_scenarios.csv: exclusivamente hipóteses matemáticas; nenhuma linha corresponde a preços ou probabilidades de um evento real.
- arithmetic_check.mjs: verificador sem rede, sem contas, sem dados externos e sem regras de trading. Recalcula cenários e recusa entradas inválidas. Executar node arithmetic_check.mjs --self-test; node arithmetic_check.mjs para emitir o CSV.
Sem snapshots integrais dos sites: referências e extrações factuais curtas permitem localizar evidência, mas não garantem imutabilidade de páginas. Verificação futura deverá guardar documentos originais e hashes com respeito às licenças, antes de promover dados a teste.
