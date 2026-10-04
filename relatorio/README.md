# Relatório do T1 (LaTeX)

Fonte do relatório técnico (E1), no formato dos relatórios anteriores do grupo e com
limite de seis páginas.

## Compilar

```bash
cd relatorio
latexmk -g -pdf relatorio.tex
```

O `-g` força a recompilação: sem ele, o `latexmk` não percebe imagens novas em `figuras/`.

Também funciona no Overleaf (envie a pasta inteira). Quando o pacote `babel` em
português está instalado, como no Overleaf, a hifenização em português é ativada
automaticamente. Sem ele, a hifenização fica desligada.

## O que falta preencher

| O quê | Onde | Como aparece no PDF |
|---|---|---|
| Texto que depende das fotos e dos resultados | busque `\preencher{` | texto vermelho entre colchetes |
| Valores das Tabelas 1, 2 e 3 | busque `\vazio` | `?` vermelho |
| Grafo da Figura 5b | `\ordemInferida` e `\imagemIntrusa` no preâmbulo | nós com `?` |
| Imagens | pasta `figuras/` (tabela abaixo) | retângulo tracejado |

Para a Figura 5b, use os índices de `metrics.json` (`order` e `rejected`), os mesmos da
matriz de conectividade. Exemplo: `\newcommand{\ordemInferida}{3,0,5,2,6,1}`.

Hoje sobra cerca de 40% da página 6. Cada imagem entra no mesmo tamanho do espaço
reservado, então a paginação só muda se o texto crescer.

## Figuras

Salve cada imagem em `figuras/` com o nome abaixo e extensão `.png`, `.jpg` ou `.pdf`.
Os caminhos da última coluna são relativos à pasta de saída do `build`.

| Nome em `figuras/` | Figura | Arquivo de origem |
|---|---|---|
| `entradas` | 2 | Montagem com as fotos de `data/minha_cena` e seus índices (feita à mão) |
| `keypoints-sift` | 3a | `keypoints/sift/<i>.jpg` |
| `keypoints-orb` | 3b | `keypoints/orb/<i>.jpg` (mesma imagem `i`) |
| `matches-antes` | 4a | `matches/<i>_<j>_before.jpg` |
| `matches-ratio` | 4b | `matches/<i>_<j>_ratio.jpg` |
| `matches-inliers` | 4c | `matches/<i>_<j>_inliers.jpg` |
| `conectividade` | 5a | `connectivity.png` |
| `progressivo-1`, `-2`, `-3` | 6 | `progressive/002.jpg`, uma etapa intermediária e a última |
| `panorama` | 7a | `panorama.png` |
| `deghost` | 7b | `deghost_comparison.png` |
| `stitcher` | 7c | `reference/panorama.png` (exige `--reference`) |

## Comandos e origem dos números

```bash
python -m panorama build data/minha_cena --output outputs/base --reference
python -m panorama compare data/minha_cena --output outputs/comparacao
```

| Trecho | Fonte |
|---|---|
| Tabela 1 | `metrics.json` → `detectors.<detector>`: média de `keypoints`, `extraction_seconds`, `accepted_pairs` |
| Tabela 2 | `metrics.json` → `tree` (pares usados) e `pairs`: `ratio_matches`, `inliers`, `inlier_rate` × 100, `mean_reprojection_px`, `symmetric_rmse_px` |
| Tabela 3 | `outputs/comparacao/comparison.json` → média de `alignment[].mean_px` por variante; `cv2.Stitcher` em `01_baseline/metrics.json` → `reference` e `reference_all_inputs` |
| Seção 5 e Figura 5b | `metrics.json` → `images`, `order`, `rejected` |
| Seção 7.3 | `metrics.json` → `final_alignment`, `overlap`, `coverage_fraction`, `changed_pixels` |
