"""Replace the four flowchart images already embedded in the explanation DOCX."""

from __future__ import annotations

from pathlib import Path

from docx import Document
from docx.oxml.ns import qn

ROOT = Path(__file__).resolve().parents[1]
DOCX = ROOT / "docs" / "Per_Title_Encoding_Code_Explanation.docx"
PNGS = [
    ROOT / "docs" / "flowcharts" / "flowchart_1_main_pipeline.png",
    ROOT / "docs" / "flowcharts" / "flowchart_2_candidate_encoding.png",
    ROOT / "docs" / "flowcharts" / "flowchart_3_pareto_hull.png",
    ROOT / "docs" / "flowcharts" / "flowchart_4_ladder_selection.png",
]


def replace_flowchart_images() -> None:
    doc = Document(str(DOCX))
    captions = ("Hình F.1.", "Hình F.2.", "Hình F.3.", "Hình F.4.")
    # Walk paragraphs: image is typically the empty paragraph immediately before the caption.
    rids: list[str] = []
    paras = list(doc.paragraphs)
    for i, para in enumerate(paras):
        text = para.text.strip()
        if not any(text.startswith(c) for c in captions):
            continue
        prev = paras[i - 1] if i else None
        if prev is None:
            continue
        blips = prev._element.findall(".//" + qn("a:blip"))
        if not blips and i >= 2:
            blips = paras[i - 2]._element.findall(".//" + qn("a:blip"))
        for blip in blips:
            rid = blip.get(qn("r:embed"))
            if rid:
                rids.append(rid)
    if len(rids) != 4:
        raise RuntimeError(f"Expected 4 flowchart blips, found {len(rids)}: {rids}")
    for rid, png in zip(rids, PNGS):
        part = doc.part.related_parts[rid]
        part._blob = png.read_bytes()
    doc.save(str(DOCX))
    print("replaced", rids)


if __name__ == "__main__":
    replace_flowchart_images()
