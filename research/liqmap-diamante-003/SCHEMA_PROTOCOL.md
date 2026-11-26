# LIQMAP003-SCHEMA — pré-registo de verificação dos Parquet públicos
Congelado em 2026-11-26 ANTES de descarregar o primeiro Parquet.

Pelo inventário PREVIOUS RUN 45776746721, o repositório HF ProbioticFarmer/hyperliquid-augmented-copytrading apresenta 391 ficheiros e 390 datas (2025-07-29 a 2026-10-13), ~6.06GB. O inventário não comprova colunas, autenticidade ou presença de posições BTC com liquidação.

Amostra pré-fixada de dois extremos das datas observadas: 2025-07-29 e 2026-10-13, ficheiros e Git LFS OIDs exatamente nos metadados originais. Fazer apenas GET sem autenticação, no máximo 35MB por ficheiro; SHA256 dos bytes e tamanho. Usa pyarrow para inspecionar nomes de colunas, tipos, contagem, BTC rows e timestamps em cada ficheiro. Nunca publicar nomes de carteiras / user IDs / moradas / dados de titulares.

Gates:
1. Se não existir coluna inequívoca de preço de liquidação real e tamanho/valor da posição BTC, ou se não houver timestamp fonte fiável ou valores com as_of > data do snapshot => SCHEMA_SOURCE_BLOCKED.
2. Se a amostra revelar mistura de fontes, posições não verificáveis, dados com timestamp posterior ao período ou duplicados impossíveis, classificar SOURCE_UNTRUSTED / INCONCLUSIVE, não inventar mapas.
3. Se colunas e cobertura passarem, autorizar apenas experimentação histórica separada com regra já congelada do LIQMAP002 (sem atribuir aos mapas HyperQuant), fornecendo estudo retrospectivo exploratório, não live GO, e controlos MOM24 e custos.
4. Não descarregar automaticamente todos os 6GB sem estimar custo/riscos; ambiente de GitHub Actions público, não usar AWS requester pays, chaves, assinaturas ou dinheiro.
