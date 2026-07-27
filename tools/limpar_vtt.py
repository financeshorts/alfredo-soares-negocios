"""Converte as legendas .vtt baixadas em texto limpo e legível.

As auto-captions do YouTube vêm com repetição de linha (rolling captions),
tags inline e marcadores '>>' de troca de falante. Este script remove tudo isso.

Uso:  python tools/limpar_vtt.py [pasta_corpus]
Saída: <corpus>/txt/<video_id>.txt  +  <corpus>/indice.json
"""
import glob
import html
import io
import json
import os
import re
import sys

SEP_ALT = '\\t'  # fallback: yt-dlp no Windows às vezes emite "\t" literal


def carregar_titulos(base):
    """Lê videolist.tsv e devolve {id: (titulo, duracao_segundos)}."""
    caminho = os.path.join(base, 'videolist.tsv')
    titulos = {}
    if not os.path.exists(caminho):
        return titulos
    for linha in io.open(caminho, encoding='utf-8', errors='replace'):
        linha = linha.rstrip('\n')
        partes = linha.split('\t')
        if len(partes) != 3:
            partes = linha.split(SEP_ALT)
        if len(partes) != 3:
            continue
        vid, dur, titulo = partes
        try:
            titulos[vid] = (titulo, float(dur))
        except ValueError:
            titulos[vid] = (titulo, 0.0)
    return titulos


def limpar_vtt(caminho):
    """Devolve o texto corrido de um arquivo .vtt, sem repetição nem marcação."""
    bruto = io.open(caminho, encoding='utf-8', errors='replace').read()

    linhas = []
    for ln in bruto.splitlines():
        if '-->' in ln:
            continue
        if ln.startswith(('WEBVTT', 'Kind:', 'Language:', 'NOTE')):
            continue
        ln = re.sub(r'<[^>]+>', '', ln)          # tags de timing inline
        ln = html.unescape(ln)
        ln = ln.replace('>>', ' | ')             # troca de falante
        ln = re.sub(r'\[[^\]]{0,30}\]', ' ', ln)  # [música], [risadas]
        ln = re.sub(r'\s+', ' ', ln).strip()
        if ln:
            linhas.append(ln)

    # remove a repetição característica das rolling captions
    saida = []
    for ln in linhas:
        if saida:
            anterior = saida[-1]
            if ln == anterior or anterior.endswith(ln):
                continue
            if ln.startswith(anterior):
                saida[-1] = ln
                continue
        saida.append(ln)

    texto = re.sub(r'\s+', ' ', ' '.join(saida)).strip()
    return re.sub(r'(\s\|\s)+', ' | ', texto)


def quebrar_em_turnos(texto):
    """Quebra o texto corrido em parágrafos por troca de falante."""
    partes = [p.strip() for p in texto.split('|') if p.strip()]
    saida = []
    for p in partes:
        p = re.sub(r'\s+', ' ', p).strip()
        if not p:
            continue
        if saida and len(saida[-1]) < 90:   # junta turnos muito curtos
            saida[-1] += ' | ' + p
        else:
            saida.append(p)
    return saida


def main():
    base = sys.argv[1] if len(sys.argv) > 1 else 'corpus'
    titulos = carregar_titulos(base)
    destino = os.path.join(base, 'txt')
    os.makedirs(destino, exist_ok=True)

    indice = []
    for caminho in sorted(glob.glob(os.path.join(base, 'vtt', '*.vtt'))):
        vid = os.path.basename(caminho).split('.')[0]
        titulo, dur = titulos.get(vid, ('(sem título)', 0.0))
        texto = limpar_vtt(caminho)
        palavras = len(texto.split())
        if palavras < 200:      # descarta legenda vazia ou quebrada
            continue

        with io.open(os.path.join(destino, vid + '.txt'), 'w', encoding='utf-8') as f:
            f.write('# %s\n' % titulo)
            f.write('# https://www.youtube.com/watch?v=%s  (%d min)\n\n' % (vid, dur // 60))
            f.write('\n\n'.join(quebrar_em_turnos(texto)) + '\n')

        indice.append({
            'id': vid,
            'titulo': titulo,
            'minutos': int(dur // 60),
            'palavras': palavras,
        })

    indice.sort(key=lambda r: -r['palavras'])
    with io.open(os.path.join(base, 'indice.json'), 'w', encoding='utf-8') as f:
        json.dump(indice, f, ensure_ascii=False, indent=1)

    print('vídeos processados:', len(indice))
    print('palavras totais:', sum(r['palavras'] for r in indice))
    print('saída:', destino)


if __name__ == '__main__':
    main()
