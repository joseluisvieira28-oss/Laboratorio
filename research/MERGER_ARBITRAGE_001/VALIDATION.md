# Verificação e proveniência
- Base main: 75fb36c8337c3221b7551c513e049cd472dad231, árvore 844f8acb61768bd832bad7e677bb2524991ad8f2.
- Protocolo: commit 3c919efadcb41219920f23058c45aef47f90bc86; data do servidor 2026-10-20T10:38:34Z; árvore 5f9ce471373b8b085e3932d4b1c588a09bdf6a94.
- A recolha web começou depois da publicação do protocolo, nesta conversa. Sem ficheiros de estudos ou holdouts lidos; apenas nomes de caminhos e metadados da árvore remota antes do freeze.
- Branch exclusiva, sem merge e sem alterações em workflows. A publicação dos resultados acrescenta apenas research/MERGER_ARBITRAGE_001/*.
- Ferramenta web: comunicados e filings são fontes primárias; artigo científico original como evidência externa. Páginas Yahoo ATVI/TWTR falharam; circular ESTV PDF falhou. sources.csv distingue papéis.
- node arithmetic_check.mjs --self-test: PASS, 12 verificações de limites, cenários analíticos, rejeição de dados ausentes e sensibilidade de custos/prazo.
- node arithmetic_check.mjs: 70 linhas sintéticas. Não é backtest. Falta validação independente, dados de mercado autenticados, universo completo, carteira e fiscalidade individual.
- A auditoria de integridade final compara a árvore com a base: nenhum caminho fora do prefixo autorizado deve mudar e o protocolo deve manter o mesmo blob.
