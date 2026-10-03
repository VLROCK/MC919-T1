# Rastreabilidade do T1

| Item | Implementação / evidência | O que depende das fotos |
|---|---|---|
| 1.1–1.4 | `data/minha_cena/README.md`, `docs/coleta.md` | Coleta de ≥6 fotos, movimento, iluminação, local e dispositivo |
| 2.1 | SIFT, ORB, AKAZE em `features.py` | Escolher com base no conjunto real |
| 2.2/2.4 | `keypoints/<detector>/*.jpg`, rich keypoints | Inserir figuras no relatório |
| 2.3 | Comparação SIFT/ORB padrão; métricas por detector | Justificar escolha com tempo, distribuição e inliers |
| 3.1/3.2 | BF L2/Hamming, ratio e limiar no JSON | Discutir adequação do limiar |
| 3.3 | Matches antes/ratio/inliers | Selecionar par ilustrativo |
| 3.4 | Estatísticas e imagens de correspondências | Discutir erros reais, texturas e movimento |
| 4.1 | Leitura sem EXIF, nomes apenas como rótulos | Embaralhar nomes e demonstrar |
| 4.2 | Matriz de inliers + critérios de aresta | Conferir ligações espúrias |
| 4.3 | Componente, árvore máxima e ordem espacial | Validar sequência visual e reverso equivalente |
| 4.4 | Rejeição de componentes menores, lista no JSON | Incluir intrusa real de outra cena |
| 4.5 | `connectivity.csv/.png`, `order`, `tree` | Figuras e comentário no relatório |
| 5.1/5.2 | RANSAC OpenCV, warpPerspective / remap | Conferir geometria |
| 5.3 | Taxa, erro médio, RMSE simétrico por par | Tabela dos pares usados |
| 5.4 | `progressive/*.jpg` | Escolher estágios |
| 6.1/6.2 | Feathering e multibanda próprios | Conferir emendas |
| 6.3 | Inconsistência + seleção de fonte | Conferir fantasmas no objeto real |
| 6.4 | `deghost_comparison.png`, mesma ROI, 2× | Ajustar `--roi` se automático não destacar movimento |
| 6.5 | Erro geométrico, overlap, cobertura, fechamento | Avaliação visual de retas, distorção e duplicações |
| X1 | Bundle opcional; baseline preservado | Comparar antes/depois sem prometer melhora |
| X2 | Cilindro/esfera, longitude periódica, `--full-360` | Capturar volta completa; suporte depende da cena |
| X3 | Ganhos globais opcionais | Comparar exposição igual/diferente |
| X4 | `cv2.Stitcher`, status e imagens | Avaliar qualidade visual e eventual falha |

## Entregáveis e critérios

- E1: relatório final em PDF de até **seis páginas**. `relatorio.md` é roteiro, não
  PDF final. Deve ser finalizado com imagens, resultados e análise reais.
- E2: panoramas gerados e demonstração em aula. O programa gera PNG e galeria.
- E3: código executável automático a partir de pasta fora de ordem: CLI `build`.
- E4: apresentação oral de **20–25 minutos**, com slides. `apresentacao.md` é roteiro
  temporizado; os slides finais dependem das evidências reais e do grupo.

Pesos: qualidade técnica 25%; ordenação/deghosting 20%; relatório 20%; participação
e apresentação 25%; criatividade/desafios 10%. Nenhuma ferramenta verifica por si só
participação equilibrada, qualidade da coleta ou clareza da exposição oral.
