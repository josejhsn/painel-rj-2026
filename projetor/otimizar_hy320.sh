#!/usr/bin/env bash
# Otimizacao do projetor Magcubic HY320 (Android 13) via ADB sem fio.
# Roda no Termux (tablet Android) ou em qualquer Linux/macOS com adb instalado.
#
# Uso:  bash otimizar_hy320.sh IP_DO_PROJETOR
# Ex.:  bash otimizar_hy320.sh 192.168.0.25
#
# Antes de rodar, no projetor:
#   Configuracoes > Sobre > toque 7x em "Numero da versao"
#   Configuracoes > Sistema > Opcoes do desenvolvedor:
#       Depuracao USB = ligada ; Depuracao sem fio / ADB pela rede = ligada
#
# No Termux (instalar pelo F-Droid, nao pela Play Store):
#   pkg update && pkg install android-tools
#   bash otimizar_hy320.sh 192.168.0.25

set -u
IP="${1:-}"
PORTA="${2:-5555}"
APKS="${HOME}/apks_hy320"

if [ -z "$IP" ]; then
  echo "Uso: bash $0 IP_DO_PROJETOR [porta]"; exit 1
fi
if ! command -v adb >/dev/null 2>&1; then
  echo "adb nao encontrado. No Termux: pkg install android-tools"; exit 1
fi

echo "== 1/6 Conectando em $IP:$PORTA =="
adb disconnect >/dev/null 2>&1
if ! adb connect "$IP:$PORTA" | grep -q connected; then
  echo "Falha ao conectar. Confira o IP, a depuracao sem fio e aceite o aviso na tela do projetor."; exit 1
fi
adb -s "$IP:$PORTA" wait-for-device
A="adb -s $IP:$PORTA shell"
MODELO=$($A getprop ro.product.model | tr -d '\r')
ANDROID=$($A getprop ro.build.version.release | tr -d '\r')
echo "Conectado: $MODELO / Android $ANDROID"
if [ "$MODELO" != "HY320" ]; then
  read -r -p "Modelo diferente de HY320. Continuar mesmo assim? [s/N] " r
  [ "$r" = "s" ] || exit 1
fi

echo
echo "== 2/6 Acelerando a interface (animacoes 0.5x) =="
$A settings put global window_animation_scale 0.5
$A settings put global transition_animation_scale 0.5
$A settings put global animator_duration_scale 0.5
echo "Animacoes: $($A settings get global window_animation_scale | tr -d '\r') / $($A settings get global transition_animation_scale | tr -d '\r') / $($A settings get global animator_duration_scale | tr -d '\r')"

echo
echo "== 3/6 Limpando apps de terceiros (bloatware) =="
echo "Vou listar cada app de terceiros. Responda s para REMOVER, Enter para manter."
echo "Apps essenciais (Netflix, Prime, Stremio, Aptoide, Projectivy, Downloader) sao mantidos automaticamente."
MANTER='netflix|amazon|primevideo|stremio|aptoide|projectivy|aftvnews|downloader|videolan|vlc|justplayer|drminfo|google|android|youtube|termux'
REMOVIDOS=0
for p in $($A pm list packages -3 | tr -d '\r' | sed 's/^package://'); do
  if echo "$p" | grep -qiE "$MANTER"; then
    echo "  mantendo  $p"; continue
  fi
  read -r -p "  remover $p ? [s/N] " r
  if [ "$r" = "s" ]; then
    if $A pm uninstall -k --user 0 "$p" | grep -q Success; then
      echo "    removido"; REMOVIDOS=$((REMOVIDOS+1))
    else
      $A pm disable-user --user 0 "$p" >/dev/null 2>&1 && echo "    nao da pra remover; desativado"
    fi
  fi
done
echo "Removidos: $REMOVIDOS"

echo
echo "== 4/6 Atualizador OTA (opcional) =="
echo "Nesse modelo a atualizacao OTA costuma travar em 15-20%. Desativar o atualizador evita downloads sozinhos."
OTA=$($A pm list packages | tr -d '\r' | sed 's/^package://' | grep -iE 'ota|upgrade|update' | grep -viE 'google|gms' || true)
if [ -n "$OTA" ]; then
  echo "$OTA" | while read -r p; do
    read -r -p "  desativar $p ? [s/N] " r </dev/tty
    [ "$r" = "s" ] && $A pm disable-user --user 0 "$p" >/dev/null 2>&1 && echo "    desativado (reative com: adb shell pm enable $p)"
  done
else
  echo "Nenhum atualizador encontrado pelo nome. Pulando."
fi

echo
echo "== 5/6 Instalando APKs da pasta $APKS =="
mkdir -p "$APKS"
N=$(ls "$APKS"/*.apk 2>/dev/null | wc -l)
if [ "$N" -eq 0 ]; then
  echo "Pasta vazia. Para instalar pelo script, baixe no tablet os APKs (versao Android TV) de:"
  echo "  Projectivy Launcher, Stremio Android TV, Just Player, Downloader (AFTVnews), DRM Info"
  echo "e copie para $APKS . Depois rode o script de novo."
else
  for f in "$APKS"/*.apk; do
    echo "  instalando $(basename "$f")"
    adb -s "$IP:$PORTA" install -r "$f" | tail -n1
  done
fi

echo
echo "== 6/6 Limpando cache e reiniciando =="
for p in com.netflix.ninja com.netflix.mediaclient com.amazon.amazonvideo.livingroom com.stremio.one; do
  $A pm clear --cache-only "$p" >/dev/null 2>&1 || true
done
$A sync
read -r -p "Reiniciar o projetor agora? [S/n] " r
[ "$r" = "n" ] || adb -s "$IP:$PORTA" reboot

echo
echo "Pronto. Depois do reinicio, faca no proprio projetor (nao da pra automatizar):"
echo "  - Opcoes do desenvolvedor > Limite de processos em segundo plano = no maximo 3"
echo "  - Apps > Apps padrao > Launcher = Projectivy"
echo "  - Stremio > Configuracoes > Player > player externo (Just Player)"
echo "  - Wi-Fi: conectar na rede 5 GHz"
