# Relatório do T1

O projeto mantém duas versões da mesma fonte:

- `relatorio_entrega.tex`: texto principal para o entregável E1, com identificação compacta e sem o anexo suplementar. **Confirme no PDF compilado que a versão final não excede seis páginas.**
- `relatorio.tex`: versão completa, com capa e anexo detalhado para consulta e apresentação. O enunciado não concede explicitamente páginas extras para capa ou anexo; portanto, não use este PDF longo como E1 sem autorização do professor.

## Compilar

Em um ambiente com `latexmk` e os pacotes LaTeX comuns instalados:

```powershell
cd relatorio
latexmk -g -pdf relatorio_entrega.tex
latexmk -g -pdf relatorio.tex
```

O primeiro comando gera o PDF para conferir/submeter como E1; o segundo gera a versão com anexo. A compilação também pode ser feita no Overleaf, enviando a pasta `relatorio/` inteira. Confira referências cruzadas, figuras e paginação no PDF, pois a compilação integrada do Codex nesta máquina retornou `Unable to find standard directories for platform` e não exportou um PDF para revisão visual.

O código e os resultados reproduzíveis estão em [github.com/VLROCK/MC919-T1](https://github.com/VLROCK/MC919-T1). A auditoria item a item do enunciado está em `AUDITORIA_T1.md`.

## Evidências incluídas

As figuras `figuras/progressivo-1.jpg`, `progressivo-2.jpg` e `progressivo-3.jpg` são os quadros 002, 006 e 012 da execução `outputs/relatorio_progressivo_20261005/`. Ela usou os mesmos parâmetros da base do lote, com diagnósticos completos, e reproduziu a mesma ordem e a mesma intrusa rejeitada. Os arquivos `figuras/elemento-movel-0.jpg` e `elemento-movel-3.jpg` são as vistas de entrada 0 e 3; `figuras/deghost.png` mostra a mesma região alinhada sem e com remoção de fantasmas.

O anexo mostra o panorama do quintal e o `boat5`, comparação entre ajuste global e par a par, cilindro e esfera, feathering e multibanda, sensibilidade de resolução e parâmetros, remoção de fantasmas, controle sintético e referência `cv2.Stitcher`. Os gráficos e CSVs originais estão em `experimentos/20261005/`.

Para refazer os quadros progressivos da cena própria, na raiz do repositório:

```powershell
.\.venv\Scripts\python.exe -m panorama build data/minha_cena `
  --output outputs/relatorio_progressivo_20261005 `
  --projection cylindrical --alignment bundle --exposure gain `
  --max-side 600 --nfeatures 2500 --ba-points 100 --ba-iterations 100 `
  --max-megapixels 8 --diagnostics full --seed 42
```

Os arquivos da cena disponíveis têm 1600×1200 pixels nas 12 vistas e 1599×899 na intrusa. O dispositivo informado pelo grupo é um Motorola Edge 50 Neo. As dimensões nativas do sensor não são inferíveis dos JPEGs recebidos por WhatsApp.
