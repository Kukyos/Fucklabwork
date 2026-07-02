"""Smoke test for autolab.replace_in_docx against the real EX1.docx."""

from pathlib import Path
from docx import Document

from autolab import iter_all_paragraphs, replace_in_docx

SRC = r"C:\Users\Cleo\Desktop\Labs Sem4\CN\EX1.docx"
DST = r"C:\Users\Cleo\Desktop\SHITIBUILT\AutoLAB\EX1_test_output.docx"
OLD = "URK24CS1021"
NEW = "URK24CS9999"


def count_in(path):
    doc = Document(path)
    old = new = 0
    for p in iter_all_paragraphs(doc):
        old += p.text.count(OLD)
        new += p.text.count(NEW)
    return old, new


src_old, src_new = count_in(SRC)
print(f"Source EX1.docx:  old={src_old}  new={src_new}")

n = replace_in_docx(SRC, DST, OLD, NEW)
print(f"replace_in_docx returned: {n}")

out_old, out_new = count_in(DST)
print(f"Output EX1_test:  old={out_old}  new={out_new}")
print("PASS" if out_old == 0 and out_new == src_old else "FAIL")
