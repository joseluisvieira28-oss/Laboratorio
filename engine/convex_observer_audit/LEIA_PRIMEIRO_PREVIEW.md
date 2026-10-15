# CONVEX observer audit V2 — pacote isolado

Este pacote não instala nem substitui os monitores existentes.

1. Extrair todos os ficheiros para uma pasta nova.
2. Executar `powershell -NoProfile -ExecutionPolicy Bypass -File .\VERIFICAR_PACOTE.ps1`.
3. O teste valida hashes, carrega o parent V5 e verifica sinais positivos das seis estratégias, filas SQLite temporárias e deduplicação. Tudo offline, sem secrets, sem MEXC e sem Telegram real.
4. Executar `WINDOWS_READONLY_RECEIPT.ps1` para obter hashes e estado dos monitores já instalados. Não expõe tokens/chaves.

Não executar previews sobre as pastas SQLite ativas. Não iniciar um segundo monitor com o mesmo Telegram por tentativa. Uma substituição real exige plano de paragem/backup/rollback e confirmação do operador para alterar tarefas existentes.

O pacote comprova funcionamento determinístico do código empacotado, não instalação, continuidade no PC, entrega real, paridade externa completa ou rentabilidade. Janela científica de 180 segundos preservada; fechos perdidos são registados e não convertidos retroativamente em sinais elegíveis.
