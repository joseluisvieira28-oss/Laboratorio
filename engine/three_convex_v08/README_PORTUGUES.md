# Crypto Lab V08 — MEXC Futures Windows

**Esta versão é o módulo de segurança e recuperação para o futuro executor automático. A execução real ainda NÃO está ativa.** O V07 Telegram permanece instalado e independente.

## Instalar no Windows (sem Python)

Extrai o ZIP novo, abre o PowerShell na pasta e executa, por ordem:

```powershell
powershell -NoProfile -ExecutionPolicy Bypass -File .\INSTALAR_V08.ps1
powershell -NoProfile -ExecutionPolicy Bypass -File .\VERIFICAR_V08.ps1
powershell -NoProfile -ExecutionPolicy Bypass -File .\ESTADO_V08.ps1
```

O instalador verifica o SHA256, copia o EXE autónomo para `%LOCALAPPDATA%\CryptoLab\ThreeConvexV08\` e faz um teste sintético da sequência entrada, confirmação, stop e confirmação. O segundo comando reutiliza as chaves MEXC DPAPI do Windows para leituras privadas autenticadas, **sem lançar ordens**. O terceiro mostra bloqueios de prontidão.

## Motor de segurança já construído

- SQLite persistente regista intenções e mudanças de estado antes de potenciais envios.
- SOL 5m e SOL 1h partilham o mesmo slot físico; BNB 4h usa o segundo.
- Estados de resultado desconhecido nunca permitem reenvio automático, duplicação ou reinício como se não tivesse acontecido nada.
- Validador sintético exige preço real de preenchimento, posição e stop correspondente com quantidade igual, resposta posterior ao ACK e risco modelado; falhas bloqueiam o fluxo.

## Bloqueios de ordens reais por resolver

- A MEXC documenta stop de posição como pedido separado, com atualizações de volume que podem ser assíncronas. O sistema ainda não provou proteção ativa imediatamente após uma entrada real.
- A ordem condicional da MEXC aceita um stop no pedido, mas ainda não existe prova de equivalência da entrada V5 nem de proteção atómica.
- Falta autorização de risco criptograficamente autenticada, trailing/saídas reais e recuperação de falhas comprovados.
- Falta validar paridade do sinal V5 em feed de produção e vantagem prospectiva líquida após custos.

**Nenhum LIVE GO.** Não modificar a tarefa Telegram V07 que já funciona e não partilhar credenciais neste chat.

Fontes: MEXC `/api/v1/private/stoporder/place`, `/api/v1/private/planorder/place/v2`, `/api/v1/private/order/get/{orderId}` na documentação oficial.
