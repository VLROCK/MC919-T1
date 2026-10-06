"""Figuras pontuais para as seções 2–6 do relatório, sem mudar seu LaTeX."""
from pathlib import Path
import json
import shutil
import cv2
import numpy as np
from panorama.cli import parser
from panorama.features import extract, match_all
from panorama.io import read_frames, save_image, save_json


def create(rows, output):
    for dataset,input_folder in (("quintal","data/minha_cena"),("boat5","data/benchmark_boat5")):
        row=next(r for r in rows if r["dataset"]==dataset and r["variant"]=="base")
        original=Path(row["output"])
        m=json.loads((original/"metrics.json").read_text(encoding="utf-8"))
        target=output/"evidencias"/dataset
        target.mkdir(parents=True,exist_ok=True)
        frames=read_frames(input_folder,600)
        thumbs=[]
        for i,f in enumerate(frames):
            im=cv2.resize(f.image,(240,180))
            im=cv2.copyMakeBorder(im,25,0,0,0,cv2.BORDER_CONSTANT,value=(255,255,255))
            cv2.putText(im,str(i),(8,19),0,.6,(0,0,0),1)
            thumbs.append(im)
        while len(thumbs)%4:
            thumbs.append(np.full_like(thumbs[0],255))
        save_image(target/"entradas.jpg",np.vstack([np.hstack(thumbs[k:k+4]) for k in range(0,len(thumbs),4)]))
        pair=max((p for p in m["pairs"] if p["accepted"]),key=lambda p:p["inliers"])
        i,j=pair["i"],pair["j"]
        for detector in ("sift","orb"):
            fs=extract([frames[i]],detector,2500)
            view=cv2.drawKeypoints(frames[i].image,fs[0].keypoints,None,color=(0,200,255),
                                  flags=cv2.DRAW_MATCHES_FLAGS_DRAW_RICH_KEYPOINTS)
            save_image(target/f"keypoints-{detector}.jpg",view)
        args=parser().parse_args(["build",input_folder,"--max-side","600","--nfeatures","2500"])
        cv2.setRNGSeed(42)
        selected=[frames[i],frames[j]]
        match_all(selected,extract(selected,"sift",2500),args,target/"par")
        for src,dest in (("before","antes"),("ratio","ratio"),("inliers","inliers")):
            shutil.copy2(target/"par"/"matches"/f"000_001_{src}.jpg",target/f"matches-{dest}.jpg")
        for source,dest in (("panorama.png","panorama.png"),("connectivity.png","conectividade.png"),
                            ("deghost_comparison.png","deghost.png"),("reference/panorama.png","stitcher.png")):
            if (original/source).exists():
                shutil.copy2(original/source,target/dest)
        save_json(target/"origem.json",dict(run=str(original),index_to_file=m["images"],
                    order=m["order"],rejected=m["rejected"],keypoint_image=i,match_pair=[i,j],
                    note="Matches redesenhados para o par isolado; números das tabelas vêm da execução completa original."))
