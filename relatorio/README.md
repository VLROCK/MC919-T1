# Relatório do T1 (LaTeX)

Fonte do relatório técnico (E1): capa, seis páginas de corpo e o Anexo A com as fotos.
A capa e o anexo não contam no limite de páginas.

## Compilar

```bash
cd relatorio
latexmk -g -pdf relatorio.tex
```

O `-g` força a recompilação: sem ele, o `latexmk` não percebe imagens novas em `figuras/`.
Também funciona no Overleaf (envie a pasta inteira). Quando o pacote `babel` em
português está instalado, como no Overleaf, a hifenização em português é ativada
automaticamente. Sem ele, a hifenização fica desligada.

## O que ainda falta

| O quê | Onde | Como aparece no PDF |
|---|---|---|
| Dispositivo e resolução original das fotos | busque `\preencher{` (Seção 2.1) | texto vermelho entre colchetes |
| Alinhamento progressivo (Figura 4) | `figuras/progressivo-1`, `-2`, `-3` | retângulos tracejados |
| Logotipo na capa (opcional) | `figuras/logo-unicamp` | sem logotipo enquanto não existir |

As figuras aceitam `.png`, `.jpg` ou `.pdf` e entram no tamanho do espaço reservado,
então a paginação não muda. Para gerar o alinhamento progressivo com a mesma
configuração da base dos experimentos (mesmos índices e mesma ordem):

```bash
python -m panorama build data/minha_cena --output outputs/progressivo \
  --projection cylindrical --alignment bundle --exposure gain \
  --max-side 600 --nfeatures 2500 --ba-points 100 --ba-iterations 100 \
  --max-megapixels 8 --compare-detectors --diagnostics full
```

Depois copie `progressive/002.jpg`, `006.jpg` e `012.jpg` para
`figuras/progressivo-1`, `-2` e `-3`.

## Origem das figuras e dos números

Tudo vem do lote `experimentos/20261005/` (base: cilindro, ajuste global, ganho, 600 px).

| Figura/tabela | Fonte |
|---|---|
| Figura 2 (keypoints e matches) | `evidencias/quintal/keypoints-*.jpg`, `matches-*.jpg` (vista 5 e par 5–6) |
| Figura 3a (matriz) | `evidencias/quintal/conectividade.png` |
| Figura 5 (panorama, deghost, Stitcher) | `evidencias/quintal/panorama.png`, `deghost.png`, `stitcher.png` |
| Anexo A | `evidencias/quintal/entradas.jpg` |
| Tabela 1 | `tabelas/quintal_detectores.*` e P95/tempo de `tabelas/quintal_variantes.*` |
| Tabela 2 | `tabelas/quintal_pares_arvore.*` |
| Tabela 3 | `tabelas/quintal_variantes.*` e `tabelas/boat5_variantes.*` |
| Ordem, intrusa, foco, deghost e exposição | `RESULTADOS.md` e `resultados.json` |
| Controle de deghosting | `tabelas/controle_movimento.*` |
