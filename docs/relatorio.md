# Roteiro do relatório — máximo de seis páginas

Este é um roteiro para finalizar após a coleta. Não contém resultados experimentais reais.

1. **Página 1 — objetivo e coleta.** Integrantes, local, dispositivo, condições,
   contato das seis ou mais imagens com nomes embaralhados e intrusa. Definir
   hipóteses geométricas e objeto móvel. Descrever pipeline em uma figura compacta.
2. **Página 2 — detectores e matches.** SIFT/ORB (ou AKAZE): keypoints com escala e
   orientação; tabela de contagem, tempo, pares aceitos. Justificar detector.
   Exibir antes/depois do ratio no mesmo par e informar limiar Lowe e RANSAC.
3. **Página 3 — grafo, ordem e alinhamento.** Matriz de inliers, ordem inferida,
   intrusa rejeitada, árvore utilizada. Taxa e erro médio por par; dois estágios
   de alinhamento progressivo. Explicar que reverso/ciclo podem ser equivalentes.
4. **Página 4 — composição e movimento.** Panorama, recorte ampliado lado a lado
   com/sem deghosting e parâmetros iguais. Explicar escolha de fonte, feathering/
   multibanda e limitações. Inspecionar continuidade de linhas e objetos duplicados.
5. **Página 5 — extras e comparações.** Tabela par a par/bundle e cilindro/esfera;
   ganhos de exposição; referência Stitcher (inclusive falhas); fechamento 360°
   se a coleta permitir. Escolher figuras que mostrem diferenças reais. Tempos do
   pipeline completo e Stitcher não são benchmarks com escopo idêntico.
6. **Página 6 — discussão e conclusão.** Principais falhas, paralaxe, limitações,
   escolhas que funcionaram/não funcionaram e referências. Sintetizar contribuição
   de cada integrante e comandos necessários para reproduzir o experimento.

## Tabelas a preencher

| Detector | Keypoints totais | Tempo extração | Pares aceitos | Escolha/justificativa |
|---|---:|---:|---:|---|
| SIFT | a medir | a medir | a medir | |
| ORB | a medir | a medir | a medir | |

| Par utilizado | Matches ratio | Inliers | Taxa | Erro médio (px) | RMSE simétrico (px) |
|---|---:|---:|---:|---:|---:|
| preencher com `metrics.json/pairs` | | | | | |

| Variante | Erro geométrico | Evidência visual | Limitações observadas |
|---|---|---|---|
| Par a par / bundle | | | |
| Cilindro / esfera | | | |
| Sem / com exposição | | | |
| Próprio / Stitcher | | | |

Não usar dados sintéticos como se fossem a coleta exigida. Não afirmar remoção total
de fantasmas com base apenas em `changed_pixels`: inspecionar o objeto e o fundo.
Guardar a configuração/versões junto dos resultados. As fontes fornecidas são
T1.pdf e VC_Panorama.pdf; referências bibliográficas do material de apoio incluem
Lowe (2004), Fischler e Bolles (1981), Brown e Lowe (2007), Burt e Adelson (1983)
e Szeliski. Conferir os dados bibliográficos ao preparar a versão final.
