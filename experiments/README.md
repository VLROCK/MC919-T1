# Lotes de experimentos do T1

O plano está em `plan.py`; o lote usa 25 configurações em cada uma de duas cenas,
mais duas condições de exposição artificial e uma renomeação (53 execuções).
As variantes e seus parâmetros ficam congelados em `plan.json` antes da execução.

## Reproduzir

```powershell
python -m pip install -e ".[experiments]"
python -m experiments.download_data
python -m experiments.batch --output outputs/experimentos_novos
python -m experiments.report outputs/experimentos_novos --output relatorio/experimentos/novo
```

O programa não sobrescreve um lote. `--resume` retoma um lote cujo processo principal
foi interrompido entre execuções, preservando sucessos, falhas e timeouts já registrados.
Uma pasta de execução incompleta não é removida: use outra saída se a interrupção
ocorreu dentro de uma execução. Cada processo tem timeout de 240 s (configurável).

Os processos rodam **sequencialmente**, com uma thread no OpenCV/BLAS/OMP. Evite
outros cálculos pesados durante o lote para não contaminar os tempos. Não há cache
de descritores entre variantes. Os logs e comandos exatos ficam ao lado das saídas.

## Base controlada

- SIFT, até 2500 pontos, maior lado 600 px, Lowe .75, RANSAC 3 px, seed 42.
- Cilindro, bundle (100 pontos por par, até 100 avaliações), foco inicial .9.
- Ganho de exposição, feathering, inconsistência acima de 30, dilatação 5 px.
- Mesmas regras de aceitação do pipeline (20 inliers, taxa .3, cobertura .01).
- Diagnósticos compactos; sem executar outros detectores dentro do mesmo panorama.

As mudanças são individuais, salvo: `projection_planar_pairwise` muda projeção e
alinhamento (comparar com `projection_planar_bundle`, não atribuir toda a diferença
apenas à projeção); multibanda de 3 níveis muda método e número de níveis; a comparação
de resolução escala também o limiar RANSAC para manter sua tolerância física aproximada.

| Família | Valores além da base | Pergunta |
|---|---|---|
| Detector | ORB, AKAZE | Compensa trocar qualidade/distribuição por tempo? |
| Lowe | .60, .85 | Seleção estrita perde conectividade? Seleção permissiva introduz erros? |
| RANSAC | 1.5, 6 px | O consenso cresce às custas de erro? |
| Características | 1000, 5000 | Há retorno em aumentar o número de pontos SIFT? |
| Resolução | 400, 900 px | Qual o custo/qualidade de processar mais pixels? |
| Alinhamento | par a par | O bundle reduz deriva na avaliação comum? |
| Projeção | esfera, plano | A geometria cabe no plano? Há deformação ou falha? |
| Exposição | sem ganho | Diferença de brilho está sendo tratada como movimento? |
| Blending | multibanda 3/5 níveis | Emendas ficam menos visíveis? Qual o custo? |
| Deghosting | desligado, limiares 15/60 | Seleção de fonte corrige transparência ou cria recortes? |
| Foco inicial | .60, 1.20 | O resultado depende da inicialização do bundle? |
| Semente | 7, 101 além de 42 | RANSAC altera grafo, ordem ou qualidade? |
| Exposição artificial | ganhos conhecidos, compensação off/on | Ganhos corrigem perturbação fotométrica controlada? |
| Renomeação | nomes aleatórios, mesmos bytes | Ordenação depende apenas da imagem? |

## Arquivos e medidas

`outputs/<lote>/` contém plano, inventários SHA-256, ambiente, status, comandos,
logs e panoramas individuais. `relatorio/experimentos/<nome>/` contém:

- `RESULTADOS.md`: conclusões numéricas, limites e onde usar no relatório existente.
- `resultados.json`: linhas completas consolidadas.
- `tabelas/*.csv/.md/.tex`: dados e fragmentos LaTeX para `\input`.
- `figuras/*.png/.pdf/.svg`: raster a 300 dpi e versões vetoriais.
- `evaluation_support_*.json`: pontos fixos usados para avaliar todas as variantes.

As correspondências comuns são SIFT a 600 px, ratio .65 e RANSAC 1.5 px. Todas as
geometrias são avaliadas nesses mesmos pares, inclusive arestas descartadas pelo
ajuste. Para variantes em outra resolução, as coordenadas e os erros voltam à escala
600. O denominador da fração de suporte é fixo. Falhas ou imagens perdidas não são
interpretadas como erro zero. Esse protocolo é **consistência geométrica**, sem
ground truth de homografia e sem independência estatística do treinamento.

`photo_mae` mede diferença de luminosidade nas correspondências fixas após aplicar
ganhos. Não mede diretamente qualidade de emenda. `changed_fraction` é a área
tocada pelo deghosting dividida pela área válida; também não mede acerto semântico.
Há um controle sintético opcional documentado em `controlled_motion.py` com fundo
e objeto conhecidos, para avaliar deghosting sem confundir alteração com melhoria.

`core_seconds` soma leitura, extração, matching, geometria e duas composições; exclui
a maior parte da escrita final e as referências. A fase geometria ainda inclui a
escrita de `alignment.json`. Tempos Stitcher têm escopo próprio; não são uma disputa
com custo rigorosamente idêntico. Três sementes da base fornecem desvio padrão
descritivo, não significância estatística nem repetição de todas as configurações.

