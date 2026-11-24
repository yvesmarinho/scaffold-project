<!-- Criado em: 24/11/2026 11:35 -->
<!-- Modificado em: 24/11/2026 11:13 -->

# Shell integration do terminal VS Code (zsh)

## O que o scaffold configura

Todo projeto gerado declara no `.vscode/settings.json`:

```json
"terminal.integrated.shellIntegration.enabled": true,
"terminal.integrated.shellIntegration.decorationsEnabled": "both"
```

Com isso o terminal integrado:
- detecta o início e o fim de cada comando;
- marca o resultado com decorações (sucesso/erro) na margem e na régua;
- permite navegar entre comandos (`Ctrl+Up` / `Ctrl+Down`);
- mostra o cwd atual.

Os agentes de IA (Copilot, Claude Code) também dependem da shell integration para ler a saída e o exit code dos comandos que executam.

Em um `settings.json` que já existe, o merge acrescenta essas chaves sem sobrescrever um valor que o usuário tenha definido (por exemplo, `enabled: false`).

## Fallback: instalação manual (zsh)

A injeção automática do VS Code pode falhar em alguns setups, como frameworks de zsh que reescrevem o prompt ou um `ZDOTDIR` customizado. Nesses casos, faça a instalação manual:

1. **Máquina local, sem `sudo`.** Abra o `~/.zshrc` e acrescente ao final:
   ```zsh
   [[ "$TERM_PROGRAM" == "vscode" ]] && . "$(code --locate-shell-integration-path zsh)"
   ```
2. Feche e reabra o terminal integrado do VS Code.
3. **Verificação:** rode `echo ok`. Deve aparecer uma decoração (círculo) à esquerda do comando, e passar o mouse sobre ela mostra o exit code.
4. **Se falhar:** confira se o comando `code` está no PATH (`which code`). Se não estiver, no VS Code use *Command Palette → Shell Command: Install 'code' command in PATH*.

Referência: https://code.visualstudio.com/docs/terminal/shell-integration
