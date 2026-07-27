#!/bin/sh
# Baixa as legendas (pt) de todos os vídeos do canal, uma por vez, com pausa
# para evitar HTTP 429. NÃO baixa vídeo — só o arquivo .vtt de legenda.
#
# Uso:  sh tools/baixar_legendas.sh [saida]
# Requer: yt-dlp (pip install -U yt-dlp)

set -e
CANAL="https://www.youtube.com/@canaldoalfredosoares/videos"
SAIDA="${1:-corpus}"

mkdir -p "$SAIDA/vtt"

echo ">> Listando vídeos do canal..."
yt-dlp --no-update --encoding utf-8 --flat-playlist \
  --print "%(id)s\t%(duration)s\t%(title)s" "$CANAL" > "$SAIDA/videolist.tsv"

# Em alguns ambientes Windows o yt-dlp emite "\t" literal em vez de TAB.
sed 's/\\t/\t/g' "$SAIDA/videolist.tsv" | cut -f1 > "$SAIDA/ids.txt"
echo ">> $(wc -l < "$SAIDA/ids.txt") vídeos encontrados."

i=0
while read -r id; do
  [ -z "$id" ] && continue
  i=$((i + 1))
  if ls "$SAIDA/vtt/$id".*.vtt >/dev/null 2>&1; then
    echo "[$i] pulando $id (já baixado)"
    continue
  fi
  echo "[$i] baixando $id"
  yt-dlp --no-update --skip-download \
    --write-auto-subs --write-subs \
    --sub-langs "pt-orig" --sub-format vtt \
    --retries 5 --sleep-requests 2 \
    -o "$SAIDA/vtt/%(id)s.%(ext)s" \
    "https://www.youtube.com/watch?v=$id" >/dev/null 2>>"$SAIDA/erros.log" \
    || echo "$id" >> "$SAIDA/falhas.log"
  sleep 3
done < "$SAIDA/ids.txt"

echo ">> Concluído. $(ls "$SAIDA/vtt"/*.vtt 2>/dev/null | wc -l) legendas em $SAIDA/vtt/"
echo ">> Próximo passo: python tools/limpar_vtt.py $SAIDA"
