# Auditoria do relatório contra T1.pdf

Conferência realizada sobre `T1.pdf` (enunciado) e `relatorio.tex`, com as evidências em `figuras/` e `experimentos/20261005/`. As instruções do PDF são critérios do trabalho; não são instruções do usuário para ações fora deste projeto.

| Critério do T1 | Evidência no relatório | Estado |
|---|---|---|
| E1, relatório técnico de até 6 páginas em PDF | `relatorio_entrega.tex` omite capa isolada e anexo; `relatorio.tex` mantém versão completa | **Pendente de verificar paginação no PDF compilado** |
| E2, panoramas automáticos para mostrar em aula | Panorama próprio e benchmark no texto/anexo; PNGs completos em `experimentos/20261005/evidencias/` | Resultados disponíveis; demonstração em aula depende do grupo |
| E3, código executável para pasta fora de ordem, sem intervenção manual | Comando CLI na Introdução, ordem por grafo, teste com nomes aleatórios, link GitHub | Contemplado no texto e no repositório |
| E4, apresentação oral de 20–25 min com slides | É entregável separado, não seção exigida do relatório | Depende da apresentação do grupo |
| 1.1–1.4, coleta própria, ao menos 6 vistas, movimento, local, aparelho e observações | Seção Coleta e anexo suplementar: 12 vistas, árvore, quintal, Motorola Edge 50 Neo, dimensão dos JPEGs | Contemplado; resolução nativa não verificável |
| 2.1–2.4, keypoints, escala/orientação, dois detectores e justificativa | Seção Detecção, Tabela de detectores, Figura de SIFT/ORB | Contemplado |
| 3.1–3.4, matcher, ratio, antes/depois e dificuldades | Seção Emparelhamento, limiar 0,75, Figura de matches, vegetação e movimento | Contemplado |
| 4.1–4.5, nomes embaralhados, sem EXIF, matriz/grafo, ordem, intrusa rejeitada | Seção Ordenação, matriz, sequência 0–3–…–10, intrusa 12 | Contemplado |
| 5.1–5.4, homografia RANSAC, alinhamento, taxas/erros por par, progressão | Seção Alinhamento, Tabela com 11 pares e Figura progressiva real | Contemplado |
| 6.1–6.5, composição, blending, deghosting, recorte lado a lado e avaliação | Seção Composição, Figura com recorte de árvore, métricas e limitações | Contemplado |
| X1, ajuste global | Seção Extras e comparação com encadeamento par a par | Contemplado |
| X2, projeção cilíndrica/esférica e 360° se imagens permitirem | Seção Extras e anexo; fotos reais cobrem arco; 360° validado apenas em dados sintéticos | Contemplado com ressalva explícita |
| X3, exposição | Seção Extras e experimento com ganhos artificiais conhecidos | Contemplado |
| X4, referência pronta | Figura e discussão de `cv2.Stitcher` | Contemplado |

## Ajustes feitos e limites de interpretação

- A antiga afirmação de que capa e anexo “não contam” foi retirada: o enunciado só diz **até seis páginas (PDF)**, sem exceção expressa. A versão completa é suplemento; confira o PDF curto antes de entregar.
- Os quadros progressivos não são mais marcadores: foram gerados na configuração base e reproduziram a mesma ordem e rejeição da intrusa.
- A coleta registra o aparelho informado pelo grupo e a dimensão dos arquivos efetivamente usados, sem apresentar esses valores como especificação nativa da câmera.
- A análise de resolução distingue mediana, P95 e tempo, e explicita que o limiar RANSAC foi escalado com a resolução. As métricas usam correspondências fixas a 600 px, não um gabarito independente.
- A comparação sem/com deghosting evidencia a árvore, mas a seleção de fonte não garante remoção correta de todo objeto móvel; o controle sintético demonstra um caso adverso.
- Boat5 é benchmark público de cinco imagens, não substitui a coleta própria exigida pelo T1. O teste 360° é sintético, não uma captura real de volta completa.
