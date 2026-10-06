# Resultados e figuras para completar o relatório

Comece em **[20261005/RESULTADOS.md](20261005/RESULTADOS.md)** ou abra
**[a galeria local](20261005/index.html)** no navegador:

```powershell
Start-Process relatorio/experimentos/20261005/index.html
```

O pacote contém 53 execuções completas (incluindo 4 falhas registradas) e 15
condições controladas de composição. O relatório original `relatorio.tex` foi
preservado; não precisa incorporar todos os gráficos, especialmente com seis páginas.

## Experimentos adicionais mais úteis para a discussão

Além das técnicas já descritas no relatório, priorize:

1. **Sensibilidade a parâmetros:** ratio, RANSAC, foco e resolução. Ajuda a mostrar
   que as escolhas afetam conectividade, custo e alinhamento, em vez de apenas citar defaults.
2. **Avaliação sobre suporte comum:** compare os mesmos pontos mesmo quando o
   algoritmo exclui arestas do ajuste. Evita premiar a rejeição dos casos difíceis.
3. **Cauda do erro:** mediana junto de P95. Uma mediana melhor pode esconder
   desalinhamentos localizados; isso apareceu na comparação de detectores.
4. **Repetição de sementes e renomeação:** separa instabilidade do RANSAC de
   dependência indevida dos nomes das imagens.
5. **Exposição artificial:** alteração controlada de brilho com registro dos ganhos;
   mede o efeito da compensação num problema conhecido.
6. **Movimento artificial favorável e adverso:** demonstra que eliminar
   transparência não é a mesma coisa que recuperar o fundo correto.

Esses experimentos foram executados; comandos e resultados estão no pacote.
Como continuação opcional, seria interessante medir paralaxe por profundidade,
distorção radial com calibração e perda de sobreposição ao remover vistas.
Esses três últimos estudos **não foram executados** e exigem desenho/coleta próprios.

## Importar uma tabela no LaTeX

Exemplo a inserir em `relatorio.tex`, se o grupo escolher usar esta tabela:

```latex
\begin{table}[ht]
\centering\small
\resizebox{\linewidth}{!}{%
  \input{experimentos/20261005/tabelas/quintal_detectores.tex}}
\caption{Comparação a 600 px, com até 2500 características e os demais parâmetros fixos.}
\end{table}
```

As tabelas fornecidas são fragmentos `tabular`, não documentos para compilar isoladamente.
O CSV completo mantém toda a precisão; as tabelas legíveis arredondam a três casas.

## Importar uma figura

```latex
\begin{figure}[ht]
\centering
\includegraphics[width=\linewidth]{experimentos/20261005/figuras/quintal_sensibilidade.pdf}
\caption{Sensibilidade dos parâmetros; erro de consistência na escala comum de 600 px.}
\end{figure}
```

Prefira PDF vetorial para gráficos. As versões PNG estão a 300 dpi; SVG permite edição.
Para imagens do benchmark e deghosting, o conteúdo interno continua sendo raster,
mesmo quando exportado num contêiner PDF/SVG.

## Mapa para o documento atual

| Seção atual | Material pronto |
|---|---|
| Coleta | `evidencias/quintal/entradas.jpg`; dados de local/dispositivo continuam com o grupo |
| Detectores | `tabelas/quintal_detectores.*`; `evidencias/quintal/keypoints-*.jpg` |
| Matches | `evidencias/quintal/matches-*.jpg`; origem/índices em `origem.json` |
| Ordenação | `evidencias/quintal/conectividade.png`, ordem e intrusa em `RESULTADOS.md` |
| Homografias | `tabelas/quintal_pares_arvore.*` |
| Blending/deghost | `figuras/quintal_deghost.*` e `controle_movimento_*` |
| Extras | `*_variantes.*`, gráficos `*_alignment`, `*_focal`, `*_projection` |
| Referência pronta | `figuras/*_stitcher.*`, tempos em `tabelas/*_sementes.*` |
| Discussão | `RESULTADOS.md`, falhas e limitações metodológicas |

Nos diretórios `evidencias`, as imagens já têm os nomes esperados pelo macro
`\imagem` do relatório. Copie apenas as escolhidas para `relatorio/figuras/`, sem
misturar índices de execuções diferentes. Matches foram redesenhados sobre o par
isolado: as contagens das tabelas provêm do lote original, como informa `origem.json`.
O lote compacto não gera alinhamento progressivo; esses estágios permanecem nas
execuções anteriores em `outputs/` ou podem ser gerados com `build --diagnostics full`.

## Atenções ao preencher

- O relatório atual afirma 1200 px e 5000 pontos. O lote usa 600 px e 2500 pontos
  como base. Ajuste o texto se usar estes números.
- A base deste lote é cilindro + bundle + ganho. A tabela antiga tem base plana;
  os rótulos precisam acompanhar a configuração real.
- “Erro médio por par” (tabela de homografias) e “mediana em suporte comum” (lote)
  são métricas diferentes e não devem receber o mesmo título.
- Cilindro e esfera usam as mesmas rotações neste pipeline: seus erros de reprojeção
  podem ser idênticos apesar da aparência diferente. Compare também as figuras.
- O foco 0.6 reteve 30 arestas no quintal, contra 11 da base 0.9. A melhora observada
  inclui a mudança na seleção de atalhos antes do bundle; não isole a causa como
  uma estimativa de foco simplesmente “mais correta”.
- Cinco imagens públicas não substituem a coleta de seis fotos nem são um conjunto 360°.
- Não coloque todos os 24 gráficos no relatório: use a galeria como suplemento.

Plano e reexecução: [experiments/README.md](../../experiments/README.md).
