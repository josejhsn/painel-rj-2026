#!/usr/bin/env bash
# Versao 100% automatica para o Termux: sem perguntas, acha o projetor sozinho.
# Uso: bash auto_hy320.sh            (ou passe o IP: bash auto_hy320.sh 192.168.0.25)
set -u
LOG="$HOME/hy320.log"
exec > >(tee -a "$LOG") 2>&1
echo "===== $(date) ====="

echo "== Instalando adb (se faltar) =="
command -v adb >/dev/null 2>&1 || { pkg update -y >/dev/null 2>&1 || true; pkg install -y android-tools; }
command -v adb >/dev/null 2>&1 || { echo "Nao consegui instalar o adb."; exit 1; }
adb start-server >/dev/null 2>&1

IP="${1:-}"
if [ -z "$IP" ]; then
  echo "== Procurando o projetor na rede =="
  MEU=$(ip -4 route get 1.1.1.1 2>/dev/null | awk '{for(i=1;i<=NF;i++) if($i=="src"){print $(i+1); exit}}')
  [ -z "$MEU" ] && MEU=$(ifconfig 2>/dev/null | awk '/inet /{print $2}' | grep -v '^127' | head -n1)
  if [ -z "$MEU" ]; then echo "Nao achei o IP do tablet. Rode: bash auto_hy320.sh IP_DO_PROJETOR"; exit 1; fi
  REDE=$(echo "$MEU" | cut -d. -f1-3)
  echo "Tablet em $MEU, varrendo $REDE.0/24 na porta 5555..."
  for i in $(seq 1 254); do
    (timeout 1 bash -c "echo > /dev/tcp/$REDE.$i/5555" 2>/dev/null && echo "$REDE.$i") &
  done | sort -u > "$HOME/.hy320_cand"
  wait
  for c in $(cat "$HOME/.hy320_cand"); do
    adb disconnect >/dev/null 2>&1
    if adb connect "$c:5555" 2>/dev/null | grep -q connected; then
      sleep 2
      M=$(adb -s "$c:5555" shell getprop ro.product.model 2>/dev/null | tr -d '\r')
      if [ "$M" = "HY320" ]; then IP="$c"; break; fi
    fi
  done
  if [ -z "$IP" ]; then
    echo "Nao achei o HY320 na rede. Confira no projetor: Opcoes do desenvolvedor > Depuracao USB e Depuracao sem fio ligadas,"
    echo "e aceite o aviso 'Permitir depuracao' na tela dele. Depois rode de novo."
    exit 1
  fi
fi

adb disconnect >/dev/null 2>&1
adb connect "$IP:5555" | grep -q connected || { echo "Falha ao conectar em $IP. Aceite o aviso na tela do projetor e rode de novo."; exit 1; }
A="adb -s $IP:5555 shell"
echo "Conectado: $($A getprop ro.product.model | tr -d '\r') Android $($A getprop ro.build.version.release | tr -d '\r') em $IP"

echo "== Animacoes 0.5x =="
$A settings put global window_animation_scale 0.5
$A settings put global transition_animation_scale 0.5
$A settings put global animator_duration_scale 0.5

echo "== Removendo bloatware conhecido (lista conservadora) =="
BLOAT='tiktok|facebook|instagram|twitter|kwai|likee|snapchat|game|games|jogo|kids|chatgpt|wps|dailymotion|tver|bilibili|iqiyi|wetv|viu|zoom|teams|skype|browser|navegador|cleaner|booster|antivirus|weather|clima|news|noticia'
MANTER='netflix|amazon|primevideo|stremio|aptoide|projectivy|aftvnews|downloader|videolan|vlc|justplayer|drminfo|google|android|youtube|spotify|disney|globo|hbo|max\.|paramount|crunchyroll|plex|kodi|termux'
for p in $($A pm list packages -3 | tr -d '\r' | sed 's/^package://'); do
  if echo "$p" | grep -qiE "$MANTER"; then continue; fi
  if echo "$p" | grep -qiE "$BLOAT"; then
    if $A pm uninstall -k --user 0 "$p" 2>/dev/null | grep -q Success; then echo "  removido  $p";
    else $A pm disable-user --user 0 "$p" >/dev/null 2>&1 && echo "  desativado $p"; fi
  else
    echo "  mantido   $p"
  fi
done

echo "== Desativando atualizador OTA (trava em 15% nesse modelo) =="
for p in $($A pm list packages | tr -d '\r' | sed 's/^package://' | grep -iE '\.ota|otaupdate|systemupdate|fota|upgrade' | grep -viE 'google|gms'); do
  $A pm disable-user --user 0 "$p" >/dev/null 2>&1 && echo "  desativado $p"
done

echo "== Limpando cache dos apps de video =="
for p in $($A pm list packages | tr -d '\r' | sed 's/^package://' | grep -iE 'netflix|amazon|stremio|youtube'); do
  $A pm clear --cache-only "$p" >/dev/null 2>&1 || true
done
$A sync

echo "== Reiniciando o projetor =="
adb -s "$IP:5555" reboot
echo
echo "PRONTO. Log salvo em $LOG"
echo "Falta so, no projetor, pelo Aptoide TV: instalar 'Projectivy Launcher' e 'Stremio Android TV'."
