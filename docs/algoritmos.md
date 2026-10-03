# Algoritmos e organização do código

## Módulos

| Módulo | Responsabilidade |
|---|---|
| `cli.py` | Comandos, valores padrão, validação |
| `io.py` | Leitura sem EXIF, resize, escrita, proteção das saídas |
| `features.py` | Detectores, BF, Lowe, RANSAC, estatísticas por par |
| `geometry.py` | Projeção homogênea, intrínsecos e rotação mais próxima |
| `graph.py` | Componentes conexas, árvore máxima, ordem espacial |
| `optimize.py` | Ajuste global e erro em coordenadas das imagens |
| `warp.py` | Canvas, warpPerspective, projeções inversas curvas |
| `exposure.py` | Estimação robusta de ganhos relativos e solução global |
| `blend.py` | Feathering, pirâmides e deghosting por inconsistência |
| `diagnostics.py` | Matriz, comparação ampliada e galeria HTML |
| `reference.py` | cv2.Stitcher isolado |
| `pipeline.py` | Conecta as etapas e salva métricas |
| `experiments.py` | Ablações em pastas independentes |
| `synthetic.py` | Dados de teste com gabarito separado |

## Características e correspondências

SIFT é o padrão por fornecer descritores com robustez a escala e rotação; a escolha
deve ser confirmada no conjunto real usando ORB/AKAZE. Não afirmamos que vencerá em
toda cena. BF usa L2 para SIFT e Hamming para ORB/AKAZE. Para cada descritor, retém
o vizinho `d1` quando `d1 < ratio*d2`, seguido de unicidade do destino.

Homografias `H_ij` levam pixels da imagem i para j. OpenCV estima por RANSAC com
limiar configurável, confiança 0.999 e até 5000 iterações. A implementação de
estimação robusta é a do OpenCV, não um RANSAC autoral. Um inlier também deve ter
erro inverso ≤ 2× o limiar. A aresta é aceita por número, taxa e cobertura espacial
dos inliers; isso reduz consensos concentrados em pequenos objetos ou linhas.

`mean_reprojection_px` é a média de `||H_ij a - b||` nos inliers. O RMSE simétrico
é `sqrt(mean((||H_ij a-b||² + ||inv(H_ij)b-a||²)/2))`. A taxa usa como denominador
os matches após ratio e unicidade, não todos os keypoints.

## Grafo e ordenação

Todos os pares são avaliados. A maior componente conexa é a cena; componentes
menores são rejeitadas. Empate no tamanho das duas maiores gera erro explícito.
Esse critério pressupõe que a cena desejada seja dominante; não é um classificador
infalível de intrusas. A árvore geradora de peso máximo usa contagens de inliers
e ancora a câmera com maior soma de evidências incidentes.

No plano, cada transformação `T_i` leva pixels de i para o referencial da âncora.
Para uma aresta conhecida i→j: `T_j = T_i inv(H_ij)`. A projeção dos centros no
eixo principal (PCA) dá a sequência espacial. Nas superfícies curvas, `R_i` leva
raios da câmera ao mundo; extraímos a rotação mais próxima de `inv(K_j) H_ij K_i`
por SVD. A ordenação usa azimute dos eixos ópticos, abrindo o ciclo no maior
intervalo angular entre centros. Nomes são apenas rótulos; a reversão/início de um
ciclo não é uma pista de captura. O grafo e a geometria decidem a ordem.

Antes do bundle, verifica atalhos (arestas fora da árvore) contra o alinhamento
inicial. Rejeita os que excedem erro mediano de `max(5*ransac, 0.08*largura_máxima)`
pixels. A árvore permanece para manter conectividade. A medida e a decisão aparecem
em `tree_consistency_median_px`, `used_for_alignment` e `inconsistent_edges`.
É uma proteção contra falsos laços de textura repetida, não prova de correção:
uma aresta errada na própria árvore ou grande deriva acumulada ainda pode prejudicar
o resultado. A matriz mantém as contagens RANSAC originais para permitir a análise.

O baseline "par a par" encadeia arestas da árvore, e não uma ordem digitada pelo
usuário. Isso evita exigir uma sequência antes de conhecer a geometria. Todos os
pares usados aparecem em `tree`; a sequência de composição aparece em `order`.

## Bundle adjustment / ajuste global (X1)

No plano, o ajuste é de oito parâmetros por homografia global, âncora fixa. Minimiza
erro simétrico entre imagens, com `H_ij = inv(T_j) T_i`, usando todos os pares aceitos,
inclusive não consecutivos. É ajuste global de homografias, não reconstrução 3D.

Nas projeções curvas, ajusta três parâmetros de rotação por câmera não ancorada
e um fator focal comum: `H_ij = K_j R_j^T R_i inv(K_i)`. É o modelo de bundle
rotacional de panorama, sem translações ou pontos 3D independentes, alinhado ao
modelo apresentado no material de apoio. Principal point é o centro da imagem;
aspect ratio e distorção radial são fixos. Câmeras devem usar a mesma lente/FOV.

Usa `scipy.optimize.least_squares`, perda robusta soft-L1, escala do RANSAC,
Jacobiano numérico e âncora fixa para eliminar liberdade global. Limita/amostra
inliers por par uniformemente para controlar custo. Preserva transformações iniciais
e erros antes/depois. Só aceita solução finita que não piore o RMSE amostrado;
convergência e limite de avaliações são reportados separadamente. Não garante
melhora em dados fora da amostra; `final_alignment` avalia todos os inliers.

## Projeções e fechamento (X2)

Plano: `warpPerspective` e translação do canvas para coordenadas não negativas.
Verifica denominador da homografia nos cantos para não cruzar o infinito.

Cilindro: raio no mundo `(x,y,z)` → `theta=atan2(x,z)` e
`v=y/sqrt(x²+z²)`. Esfera: `theta=atan2(x,z)` e
`phi=atan2(y,sqrt(x²+z²))`. Multiplica ângulos/altura por uma escala em pixels.
O warp usa mapeamento inverso, `R_i^T` e intrínsecos, com `cv2.remap` em blocos.
Raios atrás da câmera são inválidos. Máscaras são geométricas, não derivadas da cor.

Em 360° a largura corresponde exatamente a `2*pi*scale`, sem coluna final repetida.
Uma vista pode contribuir dos dois lados do canvas; distâncias de feathering e
multibanda tratam o limite horizontal periodicamente. Cobertura horizontal e
evidência de fechamento são verificadas. A faixa vertical não é preenchida
artificialmente. Relevo/paralaxe podem produzir erro mesmo com o laço fechado.

## Exposição (X3)

Amostra luminosidade suavizada nos inliers (sem pixels escuros/saturados), estima
a mediana de `log(I_j/I_i)` e resolve `log(g_i)-log(g_j)=log(I_j/I_i)` por mínimos
quadrados, com ganho da âncora fixo. Limita ganhos a [0.4,2.5]. Aplica antes de
detectar inconsistências. É compensação escalar, não resposta radiométrica completa.

## Composição e deghosting

Feathering usa distâncias até a borda válida das duas fontes. Multibanda decompõe
em pirâmides Gaussianas/Laplacianas, mistura com máscara Gaussiana e reconstrói.
A composição é incremental seguindo a ordem inferida; por isso a mistura depende
da sequência, que fica registrada. Não é uma média global de todas as vistas.

Deghosting calcula diferença média absoluta BGR no overlap, aplica limiar,
dilatação e componentes conexas. Em cada componente suficientemente grande,
seleciona a fonte com maior distância média à borda. Impõe fonte única após
reconstrução multibanda para evitar vazamento de baixas frequências. Fora das regiões
detectadas, mantém blending normal. Não implementa costura ótima/graph cut: usa
a alternativa de pixels inconsistentes permitida em 6.3.

Isso reduz transparência, mas não identifica semanticamente o fundo. Pode manter um
objeto, apagar outro, deixar bordas ou conservar objetos em duas posições separadas.
Pixels do mosaico acumulado também podem conter mistura anterior. A evidência
honesta é o recorte com/sem e a inspeção de continuidade e distorções na cena real.

## Comparação de referência e métricas (X4)

`cv2.Stitcher` recebe as mesmas imagens redimensionadas; roda com a componente aceita
e também com todas as entradas. Falhas são resultados registrados. O pipeline
autoral não usa o Stitcher internamente.

Não compare RMSE de pares selecionados diferentes sem consultar `accepted`/`pairs`.
`final_alignment` mede erro por par nas imagens de entrada, não distâncias dependentes
da projeção do canvas. Diferença de cor no overlap, cobertura e erro da borda 360°
são diagnósticos; não provam continuidade de linhas nem ausência de distorção.
Tempos incluem escopos distintos, claramente registrados. A avaliação visual final
e exemplos de falha pertencem ao relatório.

Fontes conceituais: T1.pdf e VC_Panorama.pdf fornecidos pelo usuário; material de
apoio baseado em Szeliski, capítulo 8. Os algoritmos de baixo nível delegados às
bibliotecas são identificados acima; o grafo, warp curvo, ajuste, composição e
diagnósticos são código do projeto.
