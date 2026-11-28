# REDEMPTION-DIAMANTE-002 · 28/11/2026 · NO-GO

O catálogo Pendle respondeu no navegador e no terminal. Foram selecionados os primeiros 100 PT Ethereum distintos já vencidos na ordem do catálogo, consultando duas páginas. Os 100 contratos de mercado devolveram o PT correspondente via readTokens(). O censo identifica mercado, PT, YT, SY, ativo contabilístico, vencimento e ativos de saída. Zero pares externos indexados pelo DexScreener. Foram enviados pedidos de rota de 100 USDT limitados a quatro fontes externas; uma falha de indexação ou limite HTTP não prova ausência de OTC ou de outras bolsas. Os demais tamanhos ficam sem inventário cotável. A compra nativa de PT vencido foi excluída.

## Ensaios económicos

D02. wstETH Ethereum e Arbitrum One nos endereços publicados pela Lido. Compra USDT→wstETH e conversão da mesma quantidade wstETH→USDT no destino, em ambos os sentidos e quatro tamanhos. Os dois USDT pertencem a redes diferentes. No sentido Ethereum→Arbitrum todos perdem antes do bridge. No sentido inverso, a 1000 USDT sobram 0,07372 USDT após gas dos swaps. Sete dias a 2,80122% APY custam aproximadamente 0,53 USDT. Acrescem custos do bridge e eventual repatriação de USDT. Em 0% de carry este caso conserva somente 0,07372 para cobrir esses custos. Em 3%/5% o carry é aproximadamente 0,57/0,94 USDT. Preço de venda sete dias depois incerto. Across devolveu rota indisponível para o par consultado. Inventário pré-posicionado tem necessidade de capital e reposição própria.

D03. Foram consultados asset(), convertToAssets, previewRedeem e maxRedeem sobre zero e endereços públicos titulares das shares. A chamada eth_call de redeem com titular simulado verifica a perna de resgate sem assinar. Recibos incluem identidade, quantidade, taxas de rota, timestamps e estimativa eth_estimateGas. Não se assumiu que maxRedeem de um titular sem saldo representa capacidade do cofre. Também não se assumiu que o titular público é a carteira do investigador. A coluna after_three_gas_usdt deduz os dois swaps e o gas do resgate; fees e impacto cotados já estão incluídos nos outputs. Uma eventual aprovação, variação adversa e slippage adicional piorariam o caso. O primeiro conjunto tem pares de cotações separados por horas e é apenas diagnóstico. A segunda recolha e a recuperação de pedidos limitados estão em second/. Cada cotação representa uma rota indicativa, sem garantia de execução conjunta. A valorização normal das shares é rendimento por tempo de detenção.

D04. Foi simulada a conversão USDT→WETH com QuoterV2 Uniswap V3 (fee 500), ETH→stETH via get_dy do pool Curve e WETH→USDT com o mesmo bloco. Assumiu-se conversão ETH/WETH à paridade e o melhor resgate de um ETH por stETH, preço final constante. Aos quatro tamanhos o resultado antes do gas e da espera foi negativo. Na fila Lido o último pedido era 142964 e o último finalizado 142789. O volume por finalizar era 29446,536 stETH. A diferença de 175 IDs não determina prazo garantido. O NFT da fila dá direito à liquidação quando finalizado; slashing e flutuação de ETH agravam o risco em USDT. A consulta pública de ofertas NFT ao OpenSea exigiu chave; uma oferta direta sobre um NFT já finalizado continua por demonstrar.

D05. Consulta ao Chainlog do Maker/Sky e a list() dos seis leiloeiros de WSTETH-A/B, RETH-A e ETH-A/B/C. Zero lotes ativos no bloco Ethereum da segunda recolha. Falta preço de aquisição e o PnL é indeterminado nos quatro tamanhos. Uma fotografia sem leilões não estima frequência histórica nem identifica motivação de vendedores em DEX.

## Comparação e auditoria adversarial

O benchmark observado no ficheiro público de rendimentos foi Aave V3 Ethereum USDT, pool sem etiqueta Umbrella, TVL 662524632 USD, APY variável 2,80122%. É uma alternativa remunerada com risco de protocolo e USDT. Caixa sem rendimento oferece a base de 0%. O benchmark não promete taxas futuras. Choque de paridade de 1% representa cerca de 10 USDT por 1000 USDT expostos; nos percursos ETH há ainda delta ETH significativo. Não estimámos probabilidades de falha de contratos, de bridges ou de stablecoins. Os limites de slippage do router, concorrência por bloco, atraso manual e aprovações não foram convertidos em fills. A capacidade verificável limita-se aos montantes cotados no momento. Saldos mínimos, motivos de venda e filas futuras não foram extrapolados. Heterogeneidade de timestamps e diferenças de rede impedem afirmar arbitragem realizável.

PR #128 congelou investigação cbETH em amostras e critérios próprios; não reabrimos os outcomes. PR #141 classificou resgate/mint/burn como mecanismos a investigar. O closeout Pressure Mining V0.3 já classificava a convergência de PT como descritiva e o prémio fixo/variável como bloqueado antes de outcomes. PR #409 manteve NO-GO económico para os seletores históricos. Esta operação testa aquisição secundária de direitos e respetivo resgate.

## Reprodução e ficheiros

Código Python 3 com pycryptodome. Os recibos JSON preservam pedidos, respostas e tempos, incluindo erros. Na pasta descomprimida, python summarize.py recalcula o CSV offline. Para uma recolha nova usar pasta limpa, executar census.py e economic.py, depois rights.py, identity.py, external.py e curve.py. Os resultados dependem do bloco. A pasta second contém a segunda execução com a mesma implementação. O pacote inclui os dados e as versões efetivamente usadas. Nenhuma transação, carteira ligada, assinatura ou aprovação.

Fontes: https://api-v2.pendle.finance/core/docs · https://docs.pendle.finance/pendle-v2/ProtocolMechanics/YieldTokenization/PT · https://docs.lido.fi/deployed-contracts/ · https://docs.lido.fi/contracts/withdrawal-queue-erc721/ · https://docs.arbitrum.io/arbitrum-bridge/funds-not-arrived · https://yields.llama.fi/pools · https://github.com/joseluisvieira28-oss/Laboratorio/pull/410

Verificação adicional D01: o GeckoTerminal respondeu com uma lista válida para 8 de 100 endereços; zero pools nessas oito listas. As restantes respostas não contam como ausência de pools. O comparador Kyber classificou inicialmente 52 pedidos sem rota, 42 sem token indexado e 6 limitados. O DexScreener respondeu aos 100. Nenhum dos testes representa todos os venues existentes.

Na segunda recolha, onze das doze melhores rotas de entrada terminavam em mint ERC-4626. Essas rotas servem de controlo de subscrição ao NAV. O único último swap externo nesse conjunto foi sUSDe a 250 USDT, com −0,09410 USDT depois do gas. Para investigar o desconto em mercado secundário foi feita outra experiência com fontes ERC-4626 excluídas, inspecionando a última bolsa de cada rota. Os recibos distinguem os percursos.

Os quatro resultados otimistas D04 de 100 a 1000 USDT foram −0,0850 / −0,2154 / −0,4405 / −0,9199 USDT antes de custos de rede. No cross-chain inverso, a margem antes do bridge foi −0,0527 / −0,0268 / +0,0294 / +0,0737 USDT. No direto foi −0,1915 / −0,3107 / −0,4905 / −0,8850 USDT. Risco de unpeg, fonte desatualizada, smart contract, censura ou congestionamento não recebe probabilidade inventada.

## Preço secundário excluindo mint

| Cofre | USDT | Bruto | Gas estimado | Após gas | Estado |
|---|---:|---:|---:|---:|---|
| sDAI | 100 | -0.030148 | 0.070562 | -0.10071 | REJECTED_COSTS |
| sDAI | 250 | -0.065775 | 0.074813 | -0.140588 | REJECTED_COSTS |
| sDAI | 500 | -0.132388 | 0.074815 | -0.207203 | REJECTED_COSTS |
| sDAI | 1000 | -0.268131 | 0.074815 | -0.342946 | REJECTED_COSTS |
| sUSDS | 100 | -0.016137 | 0.075331 | -0.091468 | REJECTED_COSTS |
| sUSDS | 250 | -0.04059 | 0.074342 | -0.114932 | REJECTED_COSTS |
| sUSDS | 500 | -0.082004 | 0.074271 | -0.156275 | REJECTED_COSTS |
| sUSDS | 1000 | -0.167325 | 0.074809 | -0.242134 | REJECTED_COSTS |
| sUSDe | 100 | -0.008585 | 0.064846 | -0.073431 | REJECTED_COSTS |
| sUSDe | 250 | -0.029032 | 0.067578 | -0.09661 | REJECTED_COSTS |
| sUSDe | 500 | -0.047818 | 0.078127 | -0.125945 | REJECTED_COSTS |
| sUSDe | 1000 | -0.07668 | 0.094228 | -0.170908 | REJECTED_COSTS |
