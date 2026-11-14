"""Split data/text/*.txt into data/clean/chunks.jsonl, then embed them into data/clean/embeddings.npy.

Embeddings need GEMINI_API_KEY. Without it only chunks.jsonl is written and retrieval
falls back to keyword matching for the text lane.

Usage: uv run python -m pipeline.build_index
"""
import json

import numpy as np

from api import llm
from pipeline.investigations import INVESTIGATIONS
from pipeline.schema import CLEAN, TEXT

MAX_WORDS = 450
MIN_LAST = 100
NOISE = {"notifications", "share"}
BY_PSI = {inv["psi_id"]: inv for inv in INVESTIGATIONS}


def paragraphs(text: str) -> list[str]:
    lines, skip_next = [], False
    for line in text.splitlines():
        if skip_next:
            skip_next = False
            continue
        if line.strip() == "Contact(s)":  # contact names add nothing to answers
            skip_next = True
            continue
        if line.strip() in NOISE or line.startswith("Source: "):
            continue
        lines.append(line)
    return [p.strip() for p in "\n".join(lines).split("\n\n") if p.strip()]


def pack(paras: list[str]) -> list[str]:
    chunks: list[list[str]] = [[]]
    for p in paras:
        if chunks[-1] and sum(len(x.split()) for x in chunks[-1]) + len(p.split()) > MAX_WORDS:
            chunks.append([])
        chunks[-1].append(p)
    if len(chunks) > 1 and sum(len(x.split()) for x in chunks[-1]) < MIN_LAST:
        chunks[-2] += chunks.pop()
    return ["\n\n".join(c) for c in chunks]


def source_info(path) -> tuple[str, str, str]:
    """(source_id, title, source_url) for a data/text file."""
    first = path.read_text(encoding="utf-8").splitlines()
    url = first[0].removeprefix("Source: ").strip()
    if path.stem.startswith("PSI-"):
        inv = BY_PSI[path.stem]
        return inv["id"], inv["title"], url
    title = next(line.removeprefix("Title: ") for line in first if line.startswith("Title: "))
    return path.stem, title, url


def main() -> None:
    chunks = []
    for path in sorted(TEXT.glob("*.txt")):
        source_id, title, url = source_info(path)
        for n, text in enumerate(pack(paragraphs(path.read_text(encoding="utf-8"))), start=1):
            chunks.append({"chunk_id": f"{source_id}-chunk{n}", "source_id": source_id, "title": title,
                           "text": text, "source_url": url})

    CLEAN.mkdir(parents=True, exist_ok=True)
    with open(CLEAN / "chunks.jsonl", "w", encoding="utf-8") as f:
        for c in chunks:
            f.write(json.dumps(c, ensure_ascii=False) + "\n")
    print(f"chunks.jsonl: {len(chunks)} chunks from {len(list(TEXT.glob('*.txt')))} files")

    emb_path = CLEAN / "embeddings.npy"
    if not llm.available():
        emb_path.unlink(missing_ok=True)  # never leave embeddings out of step with chunks
        print("GEMINI_API_KEY not set: skipped embeddings.npy (text lane will use keyword matching)")
        return
    vectors = llm.embed([f"{c['title']}\n\n{c['text']}" for c in chunks], "RETRIEVAL_DOCUMENT")
    np.save(emb_path, vectors)
    print(f"embeddings.npy: {vectors.shape}")


if __name__ == "__main__":
    main()
