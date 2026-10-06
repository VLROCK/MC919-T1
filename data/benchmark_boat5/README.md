# Benchmark complementar — cinco vistas boat

Cinco arquivos do conjunto usado no tutorial oficial de stitching do OpenCV:
`boat1.jpg` a `boat5.jpg`, preservados byte a byte e renomeados sem ordem espacial.

- Fonte: https://github.com/opencv/opencv_extra/tree/4.x/testdata/stitching
- Tutorial: https://docs.opencv.org/4.x/d8/d19/tutorial_stitcher.html
- URLs fixadas em commit, mapa de nomes, tamanhos e SHA-256: `manifest.json`.
- README de origem: `UPSTREAM_README.md`.
- A raiz e o diretório consultados não fornecem licença individual das fotografias;
  a origem é atribuída, sem reivindicar autoria ou uma licença adicional.

Este é um benchmark complementar de arco parcial, sem homografias verdadeiras.
Não cobre 360° e não substitui a coleta de pelo menos seis fotos do T1.
O programa de panorama não lê o manifesto para inferir a ordem.

```powershell
python -m panorama build data/benchmark_boat5 --projection cylindrical --alignment bundle --exposure gain
```

Reobter os mesmos arquivos: consulte os URLs fixos no manifesto. O comando
`python -m experiments.download_data` baixa a revisão corrente apenas quando o
manifesto ainda não existe. Os dados brutos continuam ignorados pelo Git; o script
de download e esta documentação podem ser versionados separadamente.
