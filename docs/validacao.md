# Validação executada em 03/10/2026

Todos os dados abaixo são **sintéticos**. Não substituem os resultados a obter com
as fotos coletadas pelo grupo. Ambiente exato em `requirements-tested.txt`.

## Testes automatizados

Comando: `.\.venv\Scripts\python.exe -m pytest -q`.
Resultado final: **14 testes passaram**, cerca de 70 segundos neste computador.

- Projeção homogênea e inversa.
- Recuperação do fator focal e redução de erro do bundle rotacional.
- Rejeição da intrusa e direção correta das transformações da árvore.
- Projeção esférica nos dois lados do limite periódico; raios atrás da câmera.
- Rejeição de atalho que contradiz a árvore antes do bundle.
- Deghosting com feathering e multibanda sem transparência na região controlada.
- Pixels pretos válidos e preservação de áreas sem sobreposição.
- Recuperação de ganho de exposição conhecido.
- Pipeline plano completo: nomes embaralhados, seis vistas, intrusa, movimento,
  comparação SIFT/ORB, bundle, evidências e proteção contra sobrescrita.
- Entrada sem textura falha com mensagem controlada.
- Pipelines cilíndrico e esférico completos: 12 vistas, intrusa, volta completa,
  ciclo correto (a menos de origem/sentido), foco recuperado e RMSE por par < 1 px.
- Renomeação dos arquivos sem modificar a ordem espacial recuperada.

## Execuções inspecionadas

`outputs/validacao/index.html` contém oito variantes independentes, todas concluídas.
SIFT/ORB foram comparados; a referência `cv2.Stitcher` retornou sucesso tanto com
as imagens aceitas quanto incluindo a intrusa. A cena plana tem seis vistas e uma
intrusa. O bundle plano reduziu o RMSE amostrado de aproximadamente 0.0723 para
0.0711 px. Esse ganho pequeno é esperado em uma cena sintética quase exata.

O recorte `outputs/validacao/03_exposure/deghost_comparison.png` foi inspecionado:
o objeto translúcido torna-se opaco, mas posições separadas do objeto podem
permanecer. A limitação está documentada; não se afirma recuperação semântica do fundo.

`outputs/360_consistencia/` contém um ensaio esférico com um falso match global
provocado por textura repetida. A verificação da árvore rejeitou um atalho e o bundle
convergiu em quatro avaliações: RMSE amostrado de 0.3580 para 0.2656 px, fator focal
recuperado 0.75007 (gabarito 0.75), maior RMSE por par de aproximadamente 0.387 px.
As 12 vistas foram aceitas, a intrusa foi rejeitada e todas as colunas são cobertas.

`outputs/validacao_orb/` executa ORB no pipeline e compara também SIFT e AKAZE.
Os diretórios `outputs/teste_360_*` são ensaios de desenvolvimento anteriores à
checagem global; para a demonstração prefira `outputs/360_consistencia/` e
`outputs/360_cilindro_final/`. Não confundir esses testes com avaliação em fotos reais.

## Ainda depende da coleta

Qualidade visual em fotos reais, distribuição de textura, paralaxe, objeto móvel,
intrusa, exposição e cobertura 360° precisam ser conferidas com o conjunto do grupo.
O relatório PDF e os slides finais devem incorporar essas evidências e a participação
dos integrantes. Os roteiros já estão em `docs/relatorio.md` e `docs/apresentacao.md`.
