# tools/ — pipeline de extração do corpus

Scripts que reproduzem, do zero, o corpus que originou esta skill. Úteis para
**atualizar** o material quando o canal publicar vídeos novos.

Nenhuma transcrição é distribuída neste repositório — os scripts baixam as
legendas públicas direto do YouTube na máquina de quem executa.

## Requisitos

```bash
pip install -U yt-dlp
```

## Uso

```bash
sh tools/baixar_legendas.sh corpus
```

Lista os vídeos do canal e baixa **apenas as legendas** (`.vtt`), uma por vez,
com pausa entre requisições para não tomar HTTP 429. Vídeo não é baixado em
momento algum. Regravável: pula o que já existe.

```bash
python tools/limpar_vtt.py corpus
```

Converte `.vtt` em texto legível — remove tags de timing, marcadores `>>` de
troca de falante e a repetição característica das *rolling captions*. Gera
`corpus/txt/<id>.txt` e `corpus/indice.json`.

```bash
python tools/extrair_padroes.py corpus
```

Varre o corpus atrás dos padrões que alimentam os references de voz, analogias
e geração de ideias. Gera `corpus/padroes/{analogia,ideia,veredito,bordoes}.txt`.

## Estrutura gerada

```
corpus/
├── videolist.tsv        lista bruta do canal (id, duração, título)
├── ids.txt              só os ids
├── vtt/                 legendas cruas
├── txt/                 transcrições limpas e legíveis
├── indice.json          índice ordenado por tamanho
└── padroes/             trechos agrupados por tipo de padrão
```

## Limitação que importa

As legendas automáticas **não identificam quem fala**. Em episódios com
convidado, um trecho extraído pode ser do entrevistado, não do apresentador.

Por isso, na construção desta skill:

- os gatilhos de `ideia` e `veredito` foram priorizados — são típicos de quem
  está aconselhando ("eu faria", "eu não iria", "no teu lugar");
- 12 episódios de maior densidade de ensino foram lidos por inteiro, com
  atribuição conferida manualmente;
- a saída automática serviu como **pista**, nunca como fonte final.

Ao atualizar o corpus, manter esse critério: a extração aponta onde olhar, a
leitura decide o que entra.

## Notas de compatibilidade

- **Windows**: o `yt-dlp` pode emitir `\t` literal em vez de TAB no `--print`.
  Os dois scripts já tratam esse caso.
- **Encoding**: rode com `PYTHONUTF8=1` se o terminal estiver em cp1252.
- **Rate limit**: se aparecer HTTP 429, aumente o `sleep` no shell script.
