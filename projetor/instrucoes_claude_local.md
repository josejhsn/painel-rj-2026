# Tarefa: otimizar o projetor Magcubic HY320 via ADB sem fio

Voce esta rodando no Termux, num tablet Android que esta no mesmo Wi-Fi do projetor.
O projetor e um Magcubic HY320, Android 13 (build be311-13), 2 GB RAM, 16 GB.
O usuario quer que ele rode Netflix, Prime Video e Stremio sem travar.

## Faca, nesta ordem, explicando cada passo em portugues simples

1. Confirme que `adb` existe (`adb version`). Se nao: `pkg install android-tools`.
2. Pergunte ao usuario o IP do projetor (Configuracoes > Rede). Rode `adb connect IP:5555`.
   Se falhar, oriente: Configuracoes > Sobre > tocar 7x em "Numero da versao";
   Opcoes do desenvolvedor > Depuracao USB e Depuracao sem fio ligadas; aceitar o aviso na tela.
3. Rode o script `otimizar_hy320.sh` que esta nesta mesma pasta:
   `bash otimizar_hy320.sh IP`. Ele faz: animacoes 0.5x, remocao de bloatware com
   confirmacao, desativa o atualizador OTA (opcional), instala APKs da pasta ~/apks_hy320,
   limpa cache e reinicia. Acompanhe e ajude o usuario a decidir o que remover.
   Regra: nunca remover pacotes com netflix, amazon, stremio, aptoide, projectivy,
   com.android, com.google, launcher, settings, systemui, tvsettings no nome.
4. Se o script falhar em algum passo, execute o passo manualmente com adb e siga.
5. Ao final, liste os 4 ajustes manuais no projetor:
   - Opcoes do desenvolvedor > Limite de processos em segundo plano = no maximo 3
   - Apps > Apps padrao > Launcher = Projectivy (instalar pelo Aptoide TV se nao instalou)
   - Stremio Android TV > Configuracoes > Player > usar player externo (Just Player)
   - Wi-Fi na rede 5 GHz
6. Nao instale firmware de terceiros. Nao faca reset de fabrica sem o usuario pedir.
