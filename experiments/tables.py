"""Tabelas CSV/Markdown/LaTeX sem dependência de planilhas externas."""
import csv
from pathlib import Path


def format_value(value):
    if value is None:
        return "--"
    if isinstance(value, float):
        return f"{value:.3f}"
    if isinstance(value, bool):
        return "sim" if value else "não"
    return str(value)


def escape_tex(value):
    return "".join({"_":r"\_", "%":r"\%", "&":r"\&", "#":r"\#", "$":r"\$",
                    "{":r"\{", "}":r"\}", "\\":r"\textbackslash{}"}.get(c,c) for c in value)


def export(folder, name, rows, columns=None, pretty=True):
    folder.mkdir(parents=True, exist_ok=True)
    if columns is None:
        columns = [(k,k) for k in dict.fromkeys(k for row in rows for k in row)]
    with (folder/f"{name}.csv").open("w", encoding="utf-8-sig", newline="") as file:
        writer = csv.writer(file)
        writer.writerow([label for _,label in columns])
        writer.writerows([[row.get(key, "") for key,_ in columns] for row in rows])
    if not pretty:
        return
    headers = [label for _,label in columns]
    values = [[format_value(row.get(key)) for key,_ in columns] for row in rows]
    md = ["| "+" | ".join(headers)+" |", "| "+" | ".join(["---"]*len(headers))+" |"]
    md.extend("| "+" | ".join(v.replace("|","/") for v in row)+" |" for row in values)
    (folder/f"{name}.md").write_text("\n".join(md)+"\n", encoding="utf-8")
    # Fragmento inserível com \input; não é documento standalone.
    tex = [r"\begin{tabular}{"+"l"*len(columns)+"}", r"\hline",
           " & ".join(escape_tex(x) for x in headers)+r" \\ \hline"]
    tex.extend(" & ".join(escape_tex(x) for x in row)+r" \\" for row in values)
    tex.extend([r"\hline",r"\end{tabular}"])
    (folder/f"{name}.tex").write_text("\n".join(tex)+"\n", encoding="utf-8")
