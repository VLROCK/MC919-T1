"""Controle de composição com fundo conhecido e dois objetos artificiais."""
from types import SimpleNamespace
from pathlib import Path
import cv2
import numpy as np
import matplotlib.pyplot as plt
from panorama.blend import blend_pair
from panorama.io import read_frames, save_image
from .tables import export
from .plots import save, COLORS


def run(output):
    base = cv2.resize(read_frames("data/benchmark_boat5",1000)[0].image,(640,320)).astype(np.float32)
    # O controle opera em imagens já alinhadas; não testa matching nem geometria.
    ma,mb=np.zeros((320,640),bool),np.zeros((320,640),bool)
    ma[:,:500]=True;mb[:,140:]=True
    rows=[]
    fig,axes=plt.subplots(3,3,figsize=(12,7))
    for n,(case,xa,xb,contrast) in enumerate([
        ("favoravel_alto_contraste",400,210,"high"),
        ("adverso_alto_contraste",210,400,"high"),
        ("favoravel_baixo_contraste",400,210,"low")]):
        a,b=base.copy(),base.copy();moving=np.zeros(ma.shape,bool)
        for im,x in ((a,xa),(b,xb)):
            region=np.s_[120:190,x:x+40]
            im[region]=[15,20,240] if contrast=="high" else np.clip(im[region]+25,0,255)
            moving[region]=True
        methods=[("sem_deghost","feather",False,30), ("limiar15","feather",True,15),
                 ("limiar30","feather",True,30), ("limiar60","feather",True,60),
                 ("multibanda30","multiband",True,30)]
        for label,blend,deghost,threshold in methods:
            args=SimpleNamespace(full_360=False,ghost_threshold=threshold,ghost_dilate=5,
                                 ghost_min_area=25,blend=blend,bands=5)
            result,changed,_,_=blend_pair(a,b,ma,mb,args,deghost)
            delta=result[moving]-base[moving]
            da=np.mean(np.abs(result[moving]-a[moving]),axis=1)
            db=np.mean(np.abs(result[moving]-b[moving]),axis=1)
            rows.append(dict(case=case,method=label,background_mae=float(np.abs(delta).mean()),
                             background_rmse=float(np.sqrt(np.mean(delta**2))),
                             mixed_fraction=float(np.mean((da>2)&(db>2))),
                             changed_fraction=float(np.mean(changed[moving]>0))))
            save_image(output/"controle_movimento"/f"{case}_{label}.png",result)
            if label in {"sem_deghost","limiar15","limiar30"}:
                k=["sem_deghost","limiar15","limiar30"].index(label)
                axes[n,k].imshow(cv2.cvtColor(np.clip(result,0,255).astype(np.uint8),cv2.COLOR_BGR2RGB))
                axes[n,k].axis("off");axes[n,k].set_title(case+"\n"+label,fontsize=9)
        save_image(output/"controle_movimento"/f"{case}_background.png",base)
    fig.suptitle("Controle sintético: fundo conhecido, posições favoráveis/adversas e baixo contraste")
    save(fig,output/"figuras","controle_movimento_visual")
    export(output/"tabelas","controle_movimento",rows)
    fig,axes=plt.subplots(1,2,figsize=(11,4))
    for ax,metric,title in zip(axes,("background_mae","mixed_fraction"),
                               ("Erro em relação ao fundo conhecido","Fração de pixels misturados no objeto")):
        cases=list(dict.fromkeys(r["case"] for r in rows))
        labels=list(dict.fromkeys(r["method"] for r in rows))
        for k,label in enumerate(labels):
            selected=[r for r in rows if r["method"]==label]
            ax.bar(np.arange(3)+(k-2)*.16,[r[metric] for r in selected],width=.15,label=label,color=COLORS[k])
        ax.set_xticks(range(3),["favorável / alto","adverso / alto","favorável / baixo"],rotation=15)
        ax.set_title(title);ax.grid(axis="y",alpha=.2)
        ax.set_ylabel("MAE BGR (níveis 0–255)" if metric=="background_mae" else "Fração [0, 1]")
    axes[0].legend(fontsize=8)
    save(fig,output/"figuras","controle_movimento_metricas")
    return rows
