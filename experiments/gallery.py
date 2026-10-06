"""Índice local das figuras, tabelas e panoramas de cada execução."""
from html import escape
import os
from pathlib import Path


def create(rows, output):
    lines=["<!doctype html><html lang='pt-BR'><meta charset='utf-8'><title>Experimentos T1</title>",
           "<style>body{font:16px system-ui;max-width:1250px;margin:30px auto;padding:16px;color:#172d39}",
           "table{border-collapse:collapse;width:100%;font-size:13px}td,th{padding:9px;text-align:left;border-bottom:1px solid #ddd}",
           "th{background:#e5f0f5}img{max-width:100%;height:auto}a{color:#176b87}.failed{color:#a32020}",
           "details{margin:18px 0}summary{cursor:pointer;font-weight:600}select{padding:8px}</style>",
           "<h1>Experimentos de panorama — 05/10/2026</h1>",
           "<p><a href='RESULTADOS.md'>Guia e conclusões para o relatório</a> · "
           "<a href='tabelas/resultados_completos.csv'>CSV completo</a> · <a href='resultados.json'>JSON</a></p>",
           "<p>53 execuções do pipeline + 15 condições de composição controlada. "
           "Erros na escala de avaliação fixa de 600 px; não são ground truth. "
           "Falhas não são zeros. A fração de suporte deve acompanhar o erro.</p>",
           "<label>Conjunto: <select id='dataset' onchange='filterRows()'><option value=''>Todos</option>"]
    for dataset in dict.fromkeys(r["dataset"] for r in rows):
        lines.append(f"<option>{escape(dataset)}</option>")
    lines.extend(["</select></label><table><thead><tr><th>Conjunto</th><th>Variante</th><th>Status</th>"
                  "<th>Mediana px600</th><th>P95 px600</th><th>Núcleo s</th><th>Suporte</th></tr></thead><tbody>"])
    for row in rows:
        link=Path(os.path.relpath(Path(row["output"])/"index.html",output)).as_posix()
        if row["status"]!="ok":
            path=Path(row["output"])
            link=Path(os.path.relpath(path.parent/(path.name+".log"),output)).as_posix()
        cells=[escape(row["dataset"]),f"<a href='{escape(link)}'>{escape(row['variant'])}</a>",escape(row["status"])]
        cells += [f"{row[k]:.3f}" if row.get(k) is not None else "—" for k in
                  ("eval_median_px600","eval_p95_px600","core_seconds","eval_fraction")]
        lines.append(f"<tr data-dataset='{escape(row['dataset'])}' class='{row['status']}'>"+
                     "".join(f"<td>{cell}</td>" for cell in cells)+"</tr>")
    lines.append("</tbody></table><h2>Figuras prontas para usar</h2>")
    for path in sorted((output/"figuras").glob("*.png")):
        stem=path.stem
        lines.append(f"<details><summary>{escape(stem)}</summary><p>"
                     f"<a href='figuras/{stem}.png'>PNG 300 dpi</a> · <a href='figuras/{stem}.pdf'>PDF</a> · "
                     f"<a href='figuras/{stem}.svg'>SVG</a></p><img loading='lazy' src='figuras/{stem}.png'></details>")
    lines.append("<h2>Tabelas</h2><ul>")
    for path in sorted((output/"tabelas").glob("*.csv")):
        stem=path.stem
        links=f"<a href='tabelas/{stem}.csv'>CSV</a>"
        if (path.with_suffix(".tex")).exists():
            links+=f" · <a href='tabelas/{stem}.tex'>LaTeX</a> · <a href='tabelas/{stem}.md'>Markdown</a>"
        lines.append(f"<li>{escape(stem)}: {links}</li>")
    lines.append("</ul><script>function filterRows(){let v=document.getElementById('dataset').value;"
                 "document.querySelectorAll('tr[data-dataset]').forEach(r=>r.hidden=v&&r.dataset.dataset!==v);}</script></html>")
    (output/"index.html").write_text("\n".join(lines),encoding="utf-8")
