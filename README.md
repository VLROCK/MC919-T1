# MC919-T1 — Panorama — Trabalho 1 de Visão Computacional

Pipeline explícito em Python/OpenCV para as etapas 2–6 e extras X1–X4 do T1.
Recebe uma pasta fora de ordem, estima sobreposição, rejeita componentes de outra
cena, alinha e compõe o panorama. A etapa de coleta fica com você.

## Começar no Windows (PowerShell)

Abra o terminal na pasta `Trabalho1`. O ambiente `.venv` deste workspace já foi
preparado; você pode começar pelo comando de execução. Para instalar em outro computador
com Python 3.10 ou superior:

```powershell
py -m venv .venv
.\.venv\Scripts\python.exe -m pip install -e ".[test]"
```

Para reproduzir as versões usadas na validação, instale primeiro
`-r requirements-tested.txt` e depois o projeto com `-e .`.

Não precisa ativar o ambiente. Em Linux/macOS use `python3 -m venv .venv` e
`.venv/bin/python` no lugar de `.\.venv\Scripts\python.exe`.

## Onde colocar suas fotos

Coloque **no mínimo seis imagens parcialmente sobrepostas + uma intrusa de outra
cena** em `data/minha_cena/`. Pode criar outras pastas, uma por cena.

```text
data/
  minha_cena/
    foto_q.png
    foto_a.jpg
    ...                 # pelo menos seis vistas e uma intrusa
  outra_cena/
    ...
```

Não inclua resultados gerados na pasta de entrada. A leitura é apenas do nível
imediato da pasta. Formatos aceitos: JPG/JPEG, PNG, BMP e TIF/TIFF.
Nomes são usados para identificar arquivos, nunca para inferir a ordem. Não há leitura
de EXIF. Se necessário, salve as fotos com os pixels já na orientação correta.
Veja [orientações da coleta](data/minha_cena/README.md) e [ficha de coleta](docs/coleta.md).

## Gerar o primeiro panorama

```powershell
.\.venv\Scripts\python.exe -m panorama build data/minha_cena --output outputs/base
```

O padrão usa SIFT, BF, ratio 0.75, RANSAC de 3 px, homografias encadeadas numa árvore
de máxima confiança, feathering e deghosting por inconsistência. Também avalia ORB.
Cada execução salva o resultado sem deghosting no mesmo sistema de coordenadas.

**Se aparecer “projeção plana ... cruza o infinito”**, o referencial plano não
comporta a transformação estimada. Para uma varredura ampla, como girar a câmera
ao longo de um quintal, execute com projeção cilíndrica e ajuste global:

```powershell
python -m panorama build data/minha_cena --projection cylindrical --alignment bundle --exposure gain
```

Omitir `--output` cria uma pasta nova automaticamente. Não use `--full-360` a menos
que tenha fotografado a volta completa. O erro também pode indicar alinhamento
ruim: `alignment.json` preserva a geometria para diagnóstico mesmo quando o canvas
falha. Trocar de projeção não garante corrigir paralaxe ou matches incorretos.

Abra a galeria:

```powershell
Start-Process outputs/base/index.html
```

A pasta de saída **não pode existir**: isso evita sobrescrever comparações. Se omitir
`--output`, uma pasta com data/hora será criada em `outputs/`.

## Comparar os métodos sem substituir a implementação base

```powershell
.\.venv\Scripts\python.exe -m panorama compare data/minha_cena --output outputs/comparacao
Start-Process outputs/comparacao/index.html
```

O comando executa oito variantes: plano base; plano com bundle; plano com exposição;
plano com multibanda; cilindro par a par/bundle; esfera par a par/bundle. Em todas,
salva com/sem deghosting. A primeira variante também executa `cv2.Stitcher`.
Falhas individuais ficam em `comparison.json`, sem impedir as demais variantes.

As ablações fixam detector/resize/limiares conforme a CLI e variam apenas as opções
descritas. `compare` redefine projection/alignment/exposure/blend/deghost para a base
documentada; para uma combinação personalizada use `build`. Os erros de reprojeção
estão nas imagens de entrada redimensionadas, o que permite comparar modelos.

Exemplos individuais:

```powershell
# X1: ajuste global, mantendo a mesma projeção do baseline
.\.venv\Scripts\python.exe -m panorama build data/minha_cena --output outputs/bundle --alignment bundle

# X3: compensação de exposição
.\.venv\Scripts\python.exe -m panorama build data/minha_cena --output outputs/ganho --exposure gain

# Projeções curvas com ajuste de rotações e foco compartilhado
.\.venv\Scripts\python.exe -m panorama build data/minha_cena --output outputs/cilindro --projection cylindrical --alignment bundle --focal-factor 0.9
.\.venv\Scripts\python.exe -m panorama build data/minha_cena --output outputs/esfera --projection spherical --alignment bundle --focal-factor 0.9

# Blending multibanda e referência pronta (X4)
.\.venv\Scripts\python.exe -m panorama build data/minha_cena --output outputs/multibanda --blend multiband --exposure gain --reference

# Outro detector, com comparação dos três
.\.venv\Scripts\python.exe -m panorama build data/minha_cena --output outputs/orb --detector orb --compare-detectors sift orb akaze --ratio 0.8
```

## Panorama de 360° (X2)

Precisa de fotos que cubram a volta inteira, com sobreposição entre a primeira e a
última vista. Fotos de um arco parcial não viram 360° apenas mudando a opção.

```powershell
.\.venv\Scripts\python.exe -m panorama build data/cena360 --output outputs/360_cilindro --projection cylindrical --full-360 --alignment bundle --exposure gain --blend multiband --focal-factor 0.9
.\.venv\Scripts\python.exe -m panorama build data/cena360 --output outputs/360_esfera --projection spherical --full-360 --alignment bundle --exposure gain --blend multiband --focal-factor 0.9

# Comparação de cilindro par a par, cilindro bundle, esfera bundle e exposição
.\.venv\Scripts\python.exe -m panorama compare data/cena360 --output outputs/comparacao360 --full-360 --focal-factor 0.9
```

A projeção trata longitude periodicamente. O programa exige um laço no grafo, uma
aresta entre extremidades da ordem inferida e cobertura de todas as colunas; mede
a diferença de cor na borda de fechamento. Isso não garante ausência de paralaxe.
O resultado esférico cobre **360° na horizontal e apenas a faixa vertical fotografada**;
não inventa polos nem afirma cobertura de 360° × 180°.

`--focal-factor` é foco em pixels dividido pela largura de cada imagem, após resize.
Por exemplo, campo horizontal de 60° corresponde aproximadamente a 0.866:
`factor = 1 / (2*tan(FOV/2))`. O bundle curvo refina esse fator comum em [0.15, 5].
Use mesma lente, zoom e proporção de imagem nas capturas. Não usamos EXIF para estimá-lo.

## Parâmetros frequentes

| Opção | Padrão | Efeito |
|---|---:|---|
| `--max-side` | 1200 | Maior dimensão de cada entrada; todos os erros são nessa escala |
| `--detector` | sift | sift, orb ou akaze |
| `--nfeatures` | 5000 | Limite solicitado ao SIFT/ORB; AKAZE usa seu limiar próprio |
| `--ratio` | 0.75 | Lowe: menor é mais seletivo |
| `--ransac` | 3 | Limiar em pixels na imagem redimensionada |
| `--min-inliers` | 20 | Mínimo de consenso para uma aresta |
| `--min-inlier-ratio` | 0.3 | Mínimo de inliers/matches filtrados |
| `--min-coverage` | 0.01 | Fração mínima da imagem coberta pelo casco dos inliers |
| `--alignment` | pairwise | pairwise ou bundle |
| `--projection` | planar | planar, cylindrical ou spherical |
| `--exposure` | none | none ou gain |
| `--blend` | feather | feather ou multiband |
| `--bands` | 5 | Níveis máximos da pirâmide |
| `--deghost` | inconsistency | inconsistency ou none |
| `--ghost-threshold` | 30 | Diferença média por canal BGR; menor detecta mais regiões |
| `--ghost-dilate` | 5 | Margem do componente inconsistente em pixels do canvas |
| `--ghost-min-area` | 25 | Área mínima em pixels do canvas |
| `--ba-points` | 250 | Máximo de inliers amostrados por par no bundle |
| `--ba-iterations` | 150 | Limite de avaliações da função do otimizador |
| `--max-megapixels` | 12 | Limite de área do canvas, antes de alocar |
| `--roi X Y W H` | automática | Recorte da comparação, em pixels do canvas final |
| `--draw-matches` | 120 | Limite apenas para desenhar linhas; métricas usam todos |
| `--reference` | desligado | Executar cv2.Stitcher com aceitas e com todas as entradas |
| `--seed` | 42 | Semente do RANSAC/OpenCV |

Ajuda completa: `.\.venv\Scripts\python.exe -m panorama build --help`.
Para não comparar detectores numa execução exploratória, use `--compare-detectors`
sem nomes. Para a entrega, mantenha ao menos dois.

## O que é salvo

| Arquivo/pasta | Uso no trabalho |
|---|---|
| `index.html` | Galeria local, sem servidor e sem internet |
| `panorama.png` | Resultado final na projeção escolhida |
| `without_deghost.png` | Mesmo canvas, exposição e blending, sem seleção de fonte |
| `valid_mask.png` | Regiões com dados; pixels pretos da cena continuam válidos |
| `ghost_mask.png` | União das regiões em que houve seleção de fonte |
| `deghost_comparison.png` | Mesmo recorte, lado a lado, ampliado 2× |
| `connectivity.csv/.png` | Contagem de inliers entre todos os pares |
| `keypoints/<detector>/` | Escala e orientação dos pontos sobre cada imagem |
| `matches/*before.jpg` | Melhor vizinho antes do ratio |
| `matches/*ratio.jpg` | Após ratio e unicidade de destino |
| `matches/*inliers.jpg` | Consenso RANSAC e checagem inversa |
| `progressive/` | Alinhamento/composição ao acrescentar cada imagem |
| `metrics.json` | Configuração, versões, ordem, rejeitadas, homografias/rotações e métricas |
| `matching.json` | Diagnóstico de matches salvo antes do alinhamento, inclusive se este falhar |
| `alignment.json` | Geometria e erros salvos antes de construir o canvas, inclusive se este falhar |
| `reference/` | Panorama pronto com as imagens aceitas, se Stitcher tiver sucesso |
| `reference_all/` | Referência recebendo inclusive intrusa, se tiver sucesso |

Na matriz, a contagem pode ser positiva mesmo num par rejeitado: os demais critérios
estão em `metrics.json → pairs → accepted/reason`. O grafo utiliza somente os aceitos;
atalhos contraditórios com a árvore ainda podem ser excluídos do ajuste global
(`used_for_alignment`, `inconsistent_edges`).
Os índices das figuras são mapeados para nomes na galeria e em `metrics.json → images`.

O canvas preserva bordas sem dados (pretas, identificadas na máscara), para que
comparações e recortes mantenham coordenadas idênticas. Não há corte automático
que descarte parte do panorama ou altere a largura de 360°.

## Testar sem suas fotos

```powershell
.\.venv\Scripts\python.exe -m panorama demo --output data/demo_novo
.\.venv\Scripts\python.exe -m panorama build data/demo_novo --output outputs/demo_novo --alignment bundle --exposure gain --reference
.\.venv\Scripts\python.exe -m panorama demo --kind rotation360 --output data/demo360_novo
.\.venv\Scripts\python.exe -m panorama build data/demo360_novo --output outputs/demo360_novo --projection spherical --full-360 --alignment bundle --focal-factor 0.75
.\.venv\Scripts\python.exe -m pytest -q
```

O gerador coloca nomes embaralhados e uma intrusa; a cena plana inclui objeto móvel
e variação de exposição. A cena 360° simula raios de uma câmera em rotação.
`ground_truth.json` é gabarito dos testes e **não é lido pelo pipeline**.
Essas cenas não substituem a coleta exigida no T1.

## Arquitetura e entrega

Veja [documentação dos algoritmos](docs/algoritmos.md),
[mapa de requisitos do T1](docs/requisitos.md),
[validação executada](docs/validacao.md),
[roteiro do relatório de até seis páginas](docs/relatorio.md) e
[roteiro da apresentação de 20–25 minutos](docs/apresentacao.md).

Os arquivos de relatório/apresentação são roteiros, não resultados experimentais
concluídos. Fotos, metadados de coleta, inspeção visual e participação do grupo ainda
precisam ser incluídos. Não há resultados inventados para preencher essas lacunas.

## Limitações e diagnóstico

- A ordenação é **espacial**, não recuperação do instante de captura. Sem EXIF,
  ordem e reverso podem ser equivalentes; num ciclo, qualquer início pode ser correto.
- O método de ordem supõe varredura dominante de uma faixa. Cenas multifaixa, padrões
  repetidos e intrusas visualmente parecidas podem exigir outro modelo de grafo.
- Homografia pressupõe cena aproximadamente plana ou rotação da câmera. Paralaxe,
  rolling shutter e distorção de lente não são corrigidos automaticamente.
- Deghosting evita misturar fontes nas regiões detectadas, mas pode deixar contornos,
  remover um objeto ou conservar duas posições desconectadas. Inspecione o recorte;
  `ghost_mask.png` não é uma segmentação semântica de movimento.
- Para exposição muito diferente, comece por `--exposure gain`. O ganho é escalar,
  não corrige balanço de branco, saturação nem vinheta.
- Erro de canvas muito grande pode sinalizar homografia ruim ou projeção plana
  inadequada. Reduza resolução ou use cilindro/esfera antes de aumentar o limite.
- Se nada casar, confira sobreposição e textura. Não reduza todos os limiares de
  uma vez: use os matches e as estatísticas para identificar o problema.
- A busca compara todos os pares (custo quadrático no número de imagens). O canvas
  de 12 MP pode consumir mais de 1 GB com multibanda e matrizes temporárias; para
  máquinas menores comece com `--max-side 800 --max-megapixels 4`.
- `cv2.Stitcher` pode falhar; o código salva o status real em vez de apresentar uma
  comparação fictícia. Tempos da referência e do pipeline são escopos distintos:
  o próprio inclui diagnósticos e comparação de detectores; não são benchmark isolado.
