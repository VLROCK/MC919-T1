"""Consolida o lote em tabelas, figuras e um guia para o relatório existente."""
import argparse
import json
from pathlib import Path
import statistics
import numpy as np
from panorama.io import save_json
from .evaluate import build_support, summarize
from .tables import export
from .plots import comparisons, visual_panels
from .controlled_motion import run as controlled_motion
from .evidence import create as create_evidence
from .gallery import create as create_gallery


def metrics(row):
    return json.loads((Path(row["output"])/"metrics.json").read_text(encoding="utf-8"))


def table_sets(rows, folder):
    export(folder, "resultados_completos", rows, pretty=False)
    compact = [("variant", "Variante"), ("status", "Status"), ("accepted", "Imagens"),
               ("eval_median_px600", "Erro mediano px600"), ("eval_p95_px600", "P95 px600"),
               ("core_seconds", "Tempo núcleo s"), ("eval_fraction", "Suporte avaliado")]
    for dataset in ("quintal", "boat5"):
        current = [r for r in rows if r["dataset"] == dataset]
        export(folder, dataset+"_variantes", current, compact)
        chosen = [r for r in current if r["group"] in {"base","detector"}]
        export(folder, dataset+"_detectores", chosen,
               [("detector","Detector"),("keypoints_mean","Keypoints médios"),
                ("seconds_extract","Extração s"),("graph_edges","Arestas RANSAC"),
                ("eval_median_px600","Erro mediano px600")])
        base = next(r for r in current if r["variant"] == "base")
        m = metrics(base)
        keys = {frozenset(pair) for pair in m["tree"]}
        pairs = [p for p in m["pairs"] if frozenset((p["i"],p["j"])) in keys]
        pairs = [p | dict(pair=f"{p['i']}--{p['j']}", percent=100*p["inlier_rate"]) for p in pairs]
        export(folder,dataset+"_pares_arvore",pairs,[("pair","Par"),("ratio_matches","Matches"),
               ("inliers","Inliers"),("percent","Taxa %"),("mean_reprojection_px","Erro médio px"),
               ("symmetric_rmse_px","RMSE simétrico px")])
        seeds = [r for r in current if r["group"] in {"base","seed"} and r["status"] == "ok"]
        summary = []
        for key in ("eval_median_px600","eval_p95_px600","core_seconds","ref_seconds","ref_all_seconds"):
            values = [r[key] for r in seeds if r.get(key) is not None]
            if values:
                summary.append(dict(metric=key,n=len(values),mean=statistics.mean(values),
                                    std=statistics.stdev(values) if len(values)>1 else 0,
                                    minimum=min(values),maximum=max(values)))
        export(folder,dataset+"_sementes",summary)
    export(folder,"exposicao_controlada",[r for r in rows if r["dataset"]=="boat5_exposure"],
           [("exposure","Compensação"),("photo_mae","MAE fotométrico"),
            ("changed_fraction","Fração deghost"),("eval_median_px600","Erro mediano px600")])


def conclusions(rows, output):
    text = ["# Resultados dos experimentos — 05/10/2026", "",
            "Dados reais do quintal e cinco vistas públicas boat do OpenCV. "
            "Este pacote complementa `relatorio/relatorio.tex`; o texto original foi preservado.", "",
            f"Foram registradas **{len(rows)} execuções**, sendo **{sum(r['status']=='ok' for r in rows)} concluídas**. "
            "Falhas também estão nas tabelas; veja os logs antes de interpretar ausência de panorama.", "",
            "## Leituras que os dados permitem"]
    for dataset in ("quintal","boat5"):
        subset = [r for r in rows if r["dataset"]==dataset]
        base = next(r for r in subset if r["variant"]=="base")
        valid = [r for r in subset if r["status"]=="ok" and r.get("eval_fraction",0)==1]
        best = min(valid,key=lambda r:r["eval_median_px600"])
        pair = next(r for r in subset if r["variant"]=="alignment_pairwise")
        text.extend(["",f"### {dataset}",
            f"- Base: {base['accepted']} imagens aceitas, {base['rejected']} rejeitadas; "
            f"erro mediano no suporte comum {base['eval_median_px600']:.3f} px @600; "
            f"P95 {base['eval_p95_px600']:.3f} px; núcleo {base['core_seconds']:.2f} s.",
            f"- Menor mediana observada com suporte completo: `{best['variant']}`, "
            f"{best['eval_median_px600']:.3f} px. Isso não prova melhor qualidade visual nem generalização."])
        if pair["status"]=="ok":
            text.append(f"- Par a par: {pair['eval_median_px600']:.3f} px; bundle da base: "
                        f"{base['eval_median_px600']:.3f} px. Ver também P95 e os panoramas.")
        failures = [r["variant"] for r in subset if r["status"]!="ok"]
        text.append("- Variantes que falharam: "+(", ".join(failures) if failures else "nenhuma")+".")
        m = metrics(base)
        text.append("- Ordem da base (índices da matriz): `"+str(m["order"])+"`; rejeitadas: `"+str(m["rejected"])+"`.")
    stress = {r["variant"]:r for r in rows if r["dataset"]=="boat5_exposure" and r["status"]=="ok"}
    if len(stress)==2:
        text.extend(["", "### Exposição artificial",f"MAE nas mesmas correspondências: "
                     f"{stress['none']['photo_mae']:.3f} sem compensação e {stress['gain']['photo_mae']:.3f} com ganho. "
                     "Os ganhos alterados são conhecidos, mas pode haver saturação e diferenças fotométricas prévias."])
    base = metrics(next(r for r in rows if r["dataset"]=="quintal" and r["variant"]=="base"))
    shuffled = next((r for r in rows if r["dataset"]=="quintal_shuffled" and r["status"]=="ok"), None)
    if shuffled:
        m = metrics(shuffled)
        mapping = json.loads(Path("data/quintal_shuffled/manifest.json").read_text())["original_names"]
        expected = [base["images"][i] for i in base["order"]]
        actual = [mapping[m["images"][i]] for i in m["order"]]
        text.extend(["", "### Nomes embaralhados",f"Sequência equivalente à base (aceitando reverso): "
                     f"**{'sim' if actual in [expected,expected[::-1]] else 'não'}**. "
                     "Somente os nomes foram trocados; hashes das imagens são preservados."])
    text.extend(["", "## Como usar no relatório", "",
        "1. Tabela de detectores: `tabelas/quintal_detectores.csv/.tex`. Inclua AKAZE e confirme a escolha do SIFT com dados.",
        "2. Tabela de pares: `tabelas/quintal_pares_arvore.csv/.tex`, com índices da base. Não misture com outras execuções.",
        "3. Extras: `quintal_variantes` e `boat5_variantes`. A base deste lote é CILÍNDRICA, bundle, ganho, feathering; "
        "a tabela antiga do relatório usa base plana e precisa ser renomeada se receber estes números.",
        "4. Figuras: PNG 300 dpi, PDF vetorial e SVG em `figuras/`. Para seis páginas, priorize sensibilidade, "
        "comparação bundle/par a par e um recorte deghost; demais resultados podem ficar como material suplementar.",
        "5. As figuras visuais de deghost usam a MESMA ROI escolhida na base, para não selecionar recortes favoráveis a cada limiar.",
        "6. CSVs detalhados incluem falhas, suporte avaliado, parâmetros e avisos. Não trate linhas sem resultado como zero.",
        "", "## Ajustes necessários no texto atual", "",
        "- O relatório diz 1200 px e 5000 características. O lote principal usa **600 px e 2500**, com varreduras identificadas; "
        "o RANSAC muda proporcionalmente na comparação de resolução. Registre isso na metodologia.",
        "- Atualize a descrição dos extras: a verificação de consistência pode excluir atalhos; "
        "o ajuste não usa indiscriminadamente todas as arestas RANSAC.",
        "- Não descreva SIFT como universalmente superior a descritores binários. Estes ensaios permitem uma conclusão local.",
        "- Mediana menor não significa erro menor em toda a imagem. Consulte também P95: uma técnica pode melhorar "
        "a maioria dos pontos e piorar as regiões de maior desalinhamento.",
        "- O foco inicial altera tanto as rotações iniciais quanto a rejeição de atalhos antes do bundle. "
        "O ensaio de foco mede sensibilidade do pipeline completo, não somente a convergência do otimizador.",
        "- Não diga que o benchmark de cinco fotos cumpre a etapa de coleta do T1, nem que cobre 360°. "
        "É um subconjunto público complementar, sem homografias de ground truth.",
        "", "## Limites de interpretação", "",
        "O erro comum é calculado em correspondências SIFT fixas (ratio .65, RANSAC 1.5 px, escala 600), "
        "inclusive pares excluídos do ajuste de uma variante. É erro de consistência, **não ground truth nem validação independente**; "
        "pode favorecer SIFT e conter erros de correspondência. Só compare junto da fração de suporte e imagens aceitas.",
        "Fração de pixels alterados pelo deghost não mede remoção de fantasmas. Pode incluir paralaxe, brilho e nuvens. "
        "A comparação visual e a exposição controlada ajudam a separar causas, mas não fornecem segmentação verdadeira de movimento.",
        "Tempos são medidos em processos sequenciais com uma thread. Há três sementes apenas para a base, não "
        "três repetições de todas as variantes. Núcleo próprio produz duas composições (com/sem deghost); "
        "Stitcher produz uma e usa seus próprios valores internos. A comparação de tempo é operacional, não igualdade de algoritmos.",
        "A mediana e o desvio padrão com três sementes são descritivos; não há teste de significância nem intervalo de confiança.",
        "", "## Fonte pública", "",
        "[OpenCV extra, imagens boat](https://github.com/opencv/opencv_extra/tree/4.x/testdata/stitching) · "
        "[Tutorial oficial](https://docs.opencv.org/4.x/d8/d19/tutorial_stitcher.html). "
        "URLs fixadas em commit, hashes e identificação dos cinco arquivos: `data/benchmark_boat5/manifest.json`."])
    (output/"RESULTADOS.md").write_text("\n".join(text)+"\n",encoding="utf-8")


def main():
    p=argparse.ArgumentParser()
    p.add_argument("batch",type=Path);p.add_argument("--output",type=Path,required=True)
    args=p.parse_args();args.output.mkdir(parents=True,exist_ok=True)
    status=json.loads((args.batch/"status.json").read_text(encoding="utf-8"))
    plan=json.loads((args.batch/"plan.json").read_text(encoding="utf-8"))
    if len(status)!=len(plan):
        p.error("Lote ainda incompleto; aguarde ou retome as execuções antes de consolidar.")
    support={}
    for name,folder in (("quintal","data/minha_cena"),("boat5","data/benchmark_boat5")):
        support[name]=build_support(folder,args.output/f"evaluation_support_{name}.json")
    rows=[]
    for job in status:
        name="quintal" if job["dataset"].startswith("quintal") else "boat5"
        rows.append(summarize(job,*support[name]))
    save_json(args.output/"resultados.json",rows)
    table_sets(rows,args.output/"tabelas")
    comparisons(rows,args.output/"figuras");visual_panels(rows,args.output/"figuras")
    control=controlled_motion(args.output)
    create_evidence(rows,args.output)
    conclusions(rows,args.output)
    with (args.output/"RESULTADOS.md").open("a",encoding="utf-8") as file:
        file.write("\n## Controle de deghosting com fundo conhecido\n\n")
        for case in dict.fromkeys(r["case"] for r in control):
            naive=next(r for r in control if r["case"]==case and r["method"]=="sem_deghost")
            selected=next(r for r in control if r["case"]==case and r["method"]=="limiar30")
            file.write(f"- `{case}`: MAE de fundo {naive['background_mae']:.2f} sem deghost e "
                       f"{selected['background_mae']:.2f} com limiar 30; fração de mistura "
                       f"{naive['mixed_fraction']:.0%} → {selected['mixed_fraction']:.0%}.\n")
        file.write("\nSão **15 condições sintéticas de composição**, adicionais às 53 execuções completas. "
                   "No caso adverso, escolher uma única fonte elimina a transparência, mas conserva os objetos "
                   "e aumenta o erro em relação ao fundo. Isso é uma limitação observada, não uma falha omitida. "
                   "No baixo contraste, o limiar 15 detecta o objeto; 30 e 60 não o detectam. "
                   "Os objetos são retângulos artificiais sobre uma fotografia do benchmark, sem movimento real "
                   "nem erro de alinhamento. Não generalize o MAE zero do caso favorável para fotografias reais.\n")
    create_gallery(rows,args.output)
    print(f"Tabelas, gráficos e RESULTADOS.md em {args.output}")


if __name__=="__main__":
    main()
