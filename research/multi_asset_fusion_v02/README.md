# Fusion Multi-Asset V0.2 Source Recovery

Descoberta exploratória, não OOS, edge não certificado. Leia VERDICT_PT.md.
Protocolo congelado: 9c2e9456877093ecb4f74cdd8a63aabae21de0ce.

## Reprodução

Python 3.13 e numpy 2.3.5. A partir deste diretório, instalar a versão numpy num ambiente de investigação já autorizado, extrair recovery_inputs.zip (cria recovery/), e executar:

```
python fetch_monthly.py --cache archives
python run.py --cache archives --recovery recovery --out fresh-gate
python run.py --cache archives --recovery recovery --out fresh-replay --economics
```

Cada saída exige diretório novo. Código 2 bloqueia economia; código 0 confirma conclusão. Não reutilizar artefactos PASS de outra execução. Os downloads são exclusivamente os 319 pares congelados 2021-12/2022/2023. Os SHA dos mensais têm de coincidir com reference_source_audit.json. O pacote diário é oficial e não altera os mensais. Para atualizar capturas API, fazer nova revisão explícita de evidência, nunca substituir silenciosamente os corpos congelados.

O código estatístico original é preservado byte a byte em reference_replay.py e validado pelo Git blob SHA antes do gate. O seu main original não deve ser usado: run.py é o único ponto de entrada V0.2 e só chama estatística após validar todas as fontes. Os testes V0.1 podem ser repetidos em ../multi_asset_fusion_v01 com unittest discover. Os testes de recuperação requerem RECOVERY_CACHE e RECOVERY_INPUTS ou os caminhos locais originais indicados no teste. Usar temporários num diretório com acesso de escrita e limpeza.

Os hashes em SHA256SUMS.json cobrem evidência, código e resultados; o próprio manifesto tem o SHA imutável do commit Git. Não há workflow, deployment ou execução automática no PR.
