# Otimização do projetor Magcubic HY320

Arquivos para rodar no Termux (tablet Android) no mesmo Wi-Fi do projetor.

No Termux, cole esta única linha:

```
curl -fsSLo i.sh https://raw.githubusercontent.com/josejhsn/painel-rj-2026/claude/otimizar-tablet-projetor-xrp9kf/projetor/instalar.sh && bash i.sh
```

- `instalar.sh`: instala Node, adb e Claude Code, baixa os arquivos e abre o Claude com a tarefa.
- `otimizar_hy320.sh`: faz a otimização via ADB sem fio (animações, bloatware, APKs, cache).
- `instrucoes_claude_local.md`: roteiro que o Claude no tablet segue.
