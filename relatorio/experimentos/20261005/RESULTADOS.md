# Resultados dos experimentos — 05/10/2026

Dados reais do quintal e cinco vistas públicas boat do OpenCV. Este pacote complementa `relatorio/relatorio.tex`; o texto original foi preservado.

Foram registradas **53 execuções**, sendo **49 concluídas**. Falhas também estão nas tabelas; veja os logs antes de interpretar ausência de panorama.

## Leituras que os dados permitem

### quintal
- Base: 12 imagens aceitas, 1 rejeitadas; erro mediano no suporte comum 3.495 px @600; P95 11.609 px; núcleo 12.37 s.
- Menor mediana observada com suporte completo: `focal_060`, 2.233 px. Isso não prova melhor qualidade visual nem generalização.
- Par a par: 43.857 px; bundle da base: 3.495 px. Ver também P95 e os panoramas.
- Variantes que falharam: projection_planar_bundle, projection_planar_pairwise.
- Ordem da base (índices da matriz): `[0, 3, 1, 2, 7, 4, 5, 6, 11, 8, 9, 10]`; rejeitadas: `[12]`.

### boat5
- Base: 5 imagens aceitas, 0 rejeitadas; erro mediano no suporte comum 0.399 px @600; P95 2.850 px; núcleo 2.38 s.
- Menor mediana observada com suporte completo: `ratio_085`, 0.386 px. Isso não prova melhor qualidade visual nem generalização.
- Par a par: 42.666 px; bundle da base: 0.399 px. Ver também P95 e os panoramas.
- Variantes que falharam: projection_planar_bundle, projection_planar_pairwise.
- Ordem da base (índices da matriz): `[3, 0, 4, 1, 2]`; rejeitadas: `[]`.

### Exposição artificial
MAE nas mesmas correspondências: 41.525 sem compensação e 4.218 com ganho. Os ganhos alterados são conhecidos, mas pode haver saturação e diferenças fotométricas prévias.

### Nomes embaralhados
Sequência equivalente à base (aceitando reverso): **sim**. Somente os nomes foram trocados; hashes das imagens são preservados.

## Como usar no relatório

1. Tabela de detectores: `tabelas/quintal_detectores.csv/.tex`. Inclua AKAZE e confirme a escolha do SIFT com dados.
2. Tabela de pares: `tabelas/quintal_pares_arvore.csv/.tex`, com índices da base. Não misture com outras execuções.
3. Extras: `quintal_variantes` e `boat5_variantes`. A base deste lote é CILÍNDRICA, bundle, ganho, feathering; a tabela antiga do relatório usa base plana e precisa ser renomeada se receber estes números.
4. Figuras: PNG 300 dpi, PDF vetorial e SVG em `figuras/`. Para seis páginas, priorize sensibilidade, comparação bundle/par a par e um recorte deghost; demais resultados podem ficar como material suplementar.
5. As figuras visuais de deghost usam a MESMA ROI escolhida na base, para não selecionar recortes favoráveis a cada limiar.
6. CSVs detalhados incluem falhas, suporte avaliado, parâmetros e avisos. Não trate linhas sem resultado como zero.

## Ajustes necessários no texto atual

- O relatório diz 1200 px e 5000 características. O lote principal usa **600 px e 2500**, com varreduras identificadas; o RANSAC muda proporcionalmente na comparação de resolução. Registre isso na metodologia.
- Atualize a descrição dos extras: a verificação de consistência pode excluir atalhos; o ajuste não usa indiscriminadamente todas as arestas RANSAC.
- Não descreva SIFT como universalmente superior a descritores binários. Estes ensaios permitem uma conclusão local.
- Mediana menor não significa erro menor em toda a imagem. Consulte também P95: uma técnica pode melhorar a maioria dos pontos e piorar as regiões de maior desalinhamento.
- O foco inicial altera tanto as rotações iniciais quanto a rejeição de atalhos antes do bundle. O ensaio de foco mede sensibilidade do pipeline completo, não somente a convergência do otimizador.
- Não diga que o benchmark de cinco fotos cumpre a etapa de coleta do T1, nem que cobre 360°. É um subconjunto público complementar, sem homografias de ground truth.

## Limites de interpretação

O erro comum é calculado em correspondências SIFT fixas (ratio .65, RANSAC 1.5 px, escala 600), inclusive pares excluídos do ajuste de uma variante. É erro de consistência, **não ground truth nem validação independente**; pode favorecer SIFT e conter erros de correspondência. Só compare junto da fração de suporte e imagens aceitas.
Fração de pixels alterados pelo deghost não mede remoção de fantasmas. Pode incluir paralaxe, brilho e nuvens. A comparação visual e a exposição controlada ajudam a separar causas, mas não fornecem segmentação verdadeira de movimento.
Tempos são medidos em processos sequenciais com uma thread. Há três sementes apenas para a base, não três repetições de todas as variantes. Núcleo próprio produz duas composições (com/sem deghost); Stitcher produz uma e usa seus próprios valores internos. A comparação de tempo é operacional, não igualdade de algoritmos.
A mediana e o desvio padrão com três sementes são descritivos; não há teste de significância nem intervalo de confiança.

## Fonte pública

[OpenCV extra, imagens boat](https://github.com/opencv/opencv_extra/tree/4.x/testdata/stitching) · [Tutorial oficial](https://docs.opencv.org/4.x/d8/d19/tutorial_stitcher.html). URLs fixadas em commit, hashes e identificação dos cinco arquivos: `data/benchmark_boat5/manifest.json`.

## Controle de deghosting com fundo conhecido

- `favoravel_alto_contraste`: MAE de fundo 34.92 sem deghost e 0.00 com limiar 30; fração de mistura 100% → 0%.
- `adverso_alto_contraste`: MAE de fundo 58.29 sem deghost e 93.21 com limiar 30; fração de mistura 100% → 0%.
- `favoravel_baixo_contraste`: MAE de fundo 9.34 sem deghost e 9.34 com limiar 30; fração de mistura 100% → 100%.

São **15 condições sintéticas de composição**, adicionais às 53 execuções completas. No caso adverso, escolher uma única fonte elimina a transparência, mas conserva os objetos e aumenta o erro em relação ao fundo. Isso é uma limitação observada, não uma falha omitida. No baixo contraste, o limiar 15 detecta o objeto; 30 e 60 não o detectam. Os objetos são retângulos artificiais sobre uma fotografia do benchmark, sem movimento real nem erro de alinhamento. Não generalize o MAE zero do caso favorável para fotografias reais.
