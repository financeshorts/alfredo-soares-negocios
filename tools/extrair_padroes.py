"""Varre o corpus inteiro atrás dos padrões de fala que alimentam
references/voz-e-estilo.md, references/analogias.md e references/maquina-de-ideias.md.

Categorias extraídas:
  analogia  -> gatilhos "é igual", "é como se", "imagina", "é tipo", "pensa que"
  ideia     -> gatilhos de geração de negócio "e se você", "eu faria", "eu no teu lugar"
  veredito  -> gatilhos de corte "eu não iria", "esquece", "para, para", "não começa"
  bordoes   -> n-gramas frequentes e bem distribuídos entre os vídeos

Uso:  python tools/extrair_padroes.py [pasta_corpus]
Saída: <corpus>/padroes/*.txt

LIMITAÇÃO IMPORTANTE: as legendas automáticas não identificam quem fala. Em
episódios com convidado, um trecho capturado pode ser do entrevistado. Os
gatilhos de 'ideia' e 'veredito' são os mais confiáveis por serem típicos de
quem está aconselhando — mas toda saída precisa de conferência humana.
"""
import collections
import glob
import io
import os
import re
import sys

ANALOGIA = re.compile(
    r'(é igual|é como se|é tipo|imagina (?:só |que |você |tu )|pensa (?:que|só|comigo)|'
    r'é a mesma coisa|funciona igual|é que nem|parece com)', re.I)

IDEIA = re.compile(
    r'(e se (?:você|tu|vocês|a gente)|eu faria|eu no teu lugar|eu no lugar de|'
    r'por que (?:você|vocês|tu) não|tu já pensou|você já pensou|'
    r'eu viraria|eu pegaria|eu criaria|eu chegaria|'
    r'vocês? (?:tinha que|deveria|deveriam))', re.I)

VEREDITO = re.compile(
    r'(eu não iria|eu não faria|esquece|para, para|não começa|meu veredito|'
    r'a minha verdadeira opinião|eu particularmente)', re.I)

CATEGORIAS = {'analogia': ANALOGIA, 'ideia': IDEIA, 'veredito': VEREDITO}


def sentencas(texto):
    partes = re.split(r'(?<=[.?!])\s+|\s\|\s', texto)
    return [p.strip() for p in partes if p.strip()]


def contexto(sents, i, antes=1, depois=2):
    return ' '.join(sents[max(0, i - antes):min(len(sents), i + depois + 1)])


def main():
    base = sys.argv[1] if len(sys.argv) > 1 else 'corpus'
    origem = os.path.join(base, 'txt')
    destino = os.path.join(base, 'padroes')
    os.makedirs(destino, exist_ok=True)

    achados = {k: [] for k in CATEGORIAS}
    total_ngrama = collections.Counter()
    docs_ngrama = collections.Counter()

    arquivos = sorted(glob.glob(os.path.join(origem, '*.txt')))
    if not arquivos:
        print('nenhum .txt em %s — rode limpar_vtt.py antes' % origem)
        return

    for caminho in arquivos:
        bruto = io.open(caminho, encoding='utf-8').read()
        titulo = bruto.split('\n', 1)[0].lstrip('# ').strip()
        vid = os.path.basename(caminho)[:-4]
        corpo = bruto.split('\n\n', 1)[-1]
        sents = sentencas(corpo)

        for i, s in enumerate(sents):
            if len(s) < 40:
                continue
            for nome, padrao in CATEGORIAS.items():
                if padrao.search(s):
                    achados[nome].append((vid, titulo, contexto(sents, i)))

        palavras = re.sub(r'[^a-zà-ÿ\s]', ' ', corpo.lower()).split()
        vistos = set()
        for n in (3, 4, 5):
            for i in range(len(palavras) - n + 1):
                g = ' '.join(palavras[i:i + n])
                total_ngrama[g] += 1
                vistos.add(g)
        for g in vistos:
            docs_ngrama[g] += 1

    for nome, itens in achados.items():
        caminho = os.path.join(destino, nome + '.txt')
        with io.open(caminho, 'w', encoding='utf-8') as f:
            for vid, titulo, trecho in itens:
                f.write('[%s] %s\n%s\n\n' % (vid, titulo[:70], trecho[:900]))
        print('%-9s %4d trechos -> %s' % (nome, len(itens), caminho))

    n_videos = len(arquivos)
    minimo_docs = max(3, int(n_videos * 0.35))
    caminho = os.path.join(destino, 'bordoes.txt')
    with io.open(caminho, 'w', encoding='utf-8') as f:
        cand = [(g, d) for g, d in docs_ngrama.items()
                if d >= minimo_docs and total_ngrama[g] >= 40]
        cand.sort(key=lambda kv: (-kv[1], -total_ngrama[kv[0]]))
        for g, d in cand[:400]:
            f.write('%3d/%d vídeos %5dx  %s\n' % (d, n_videos, total_ngrama[g], g))
    print('%-9s %4d expressões -> %s' % ('bordoes', len(cand), caminho))


if __name__ == '__main__':
    main()
