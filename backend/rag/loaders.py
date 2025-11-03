from __future__ import annotations

import json
import re
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Dict, Iterable, List, Optional, Tuple

import yaml
from pypdf import PdfReader
from langchain_core.documents import Document


@dataclass
class LoadedDoc:
    text: str
    metadata: Dict[str, Any]


def _read_text(path: Path) -> str:
    try:
        return path.read_text(encoding="utf-8", errors="ignore")
    except Exception:
        # Fallback without encoding if needed
        return path.read_text(errors="ignore")


def load_pdf_text(path: Path) -> str:
    text = ""
    try:
        reader = PdfReader(str(path))
        for page in reader.pages:
            page_text = page.extract_text() or ""
            text += page_text + "\n"
    except Exception as e:
        print(f"[loaders] PDF read error for {path}: {e}")
    return text.strip()


def load_md_text(path: Path) -> Tuple[Dict[str, Any], str]:
    """
    Load Markdown and parse optional frontmatter (YAML between --- lines).
    Returns (frontmatter_metadata, content_without_frontmatter)
    """
    raw = _read_text(path)
    fm: Dict[str, Any] = {}
    content = raw

    # Simple frontmatter parser
    if raw.startswith("---"):
        parts = raw.split("\n", 1)[1]
        idx = parts.find("\n---")
        if idx != -1:
            fm_block = parts[:idx]
            rest = parts[idx + len("\n---") + 1 :]
            try:
                fm = yaml.safe_load(fm_block) or {}
                if not isinstance(fm, dict):
                    fm = {}
                content = rest
            except Exception:
                # Ignore malformed frontmatter
                content = raw

    return fm, content.strip()


def _flatten_yaml_to_facts(data: Any, prefix: str = "") -> List[str]:
    """
    Convert nested YAML into atomic statements for retrieval.
    Example:
      { education: [{ level: PU, institution: ABC }] }
    becomes facts like:
      "Education: level=PU; institution=ABC"
    """
    facts: List[str] = []

    if isinstance(data, dict):
        for k, v in data.items():
            key = f"{prefix}{k}" if not prefix else f"{prefix}.{k}"
            facts.extend(_flatten_yaml_to_facts(v, key))
    elif isinstance(data, list):
        for idx, v in enumerate(data):
            key = f"{prefix}[{idx}]"
            facts.extend(_flatten_yaml_to_facts(v, key))
    else:
        # Primitive
        p = prefix.replace(".", ": ")
        facts.append(f"{p}: {data}")

    return facts


def load_yaml_facts(path: Path, default_type: str = "profile") -> List[LoadedDoc]:
    """
    Load YAML file. If it is a QnA format (list of {q, a}), create one doc per pair.
    Otherwise, flatten to key-value statements.
    """
    try:
        data = yaml.safe_load(_read_text(path))
    except Exception as e:
        print(f"[loaders] YAML parse error for {path}: {e}")
        return []

    meta_base = {"source": str(path), "type": default_type, "filename": path.name}

    # Detect QnA shape
    if isinstance(data, list) and all(isinstance(x, dict) for x in data) and all(
        ("q" in x and "a" in x) for x in data
    ):
        out: List[LoadedDoc] = []
        for i, qa in enumerate(data):
            q = str(qa.get("q", "")).strip()
            a = str(qa.get("a", "")).strip()
            if not q or not a:
                continue
            text = f"Q: {q}\nA: {a}"
            out.append(LoadedDoc(text=text, metadata={**meta_base, "subtype": "qna", "idx": i}))
        return out

    # Generic profile YAML
    facts = _flatten_yaml_to_facts(data)
    if not facts:
        return []

    # Group small facts into chunks (simple concatenation)
    CHUNK_SIZE = 6
    chunks = ["\n".join(facts[i : i + CHUNK_SIZE]) for i in range(0, len(facts), CHUNK_SIZE)]

    return [LoadedDoc(text=c, metadata=meta_base.copy()) for c in chunks if c.strip()]


def load_json_facts(path: Path, default_type: str = "profile") -> List[LoadedDoc]:
    try:
        data = json.loads(_read_text(path))
    except Exception as e:
        print(f"[loaders] JSON parse error for {path}: {e}")
        return []

    # Reuse YAML flattening for JSON
    facts = _flatten_yaml_to_facts(data)
    if not facts:
        return []

    meta_base = {"source": str(path), "type": default_type, "filename": path.name}
    CHUNK_SIZE = 6
    chunks = ["\n".join(facts[i : i + CHUNK_SIZE]) for i in range(0, len(facts), CHUNK_SIZE)]
    return [LoadedDoc(text=c, metadata=meta_base.copy()) for c in chunks if c.strip()]


def load_txt(path: Path, default_type: str = "notes") -> LoadedDoc:
    return LoadedDoc(
        text=_read_text(path).strip(),
        metadata={"source": str(path), "type": default_type, "filename": path.name},
    )


def load_md(path: Path, default_type: str = "notes") -> LoadedDoc:
    fm, content = load_md_text(path)
    metadata = {"source": str(path), "type": default_type, "filename": path.name}
    if fm:
        metadata.update({k: v for k, v in fm.items() if k not in ("content",)})
    return LoadedDoc(text=content, metadata=metadata)


def to_documents(items: Iterable[LoadedDoc]) -> List[Document]:
    return [Document(page_content=i.text, metadata=i.metadata) for i in items if i.text.strip()]


def build_documents_from_data_dir(data_dir: Path) -> List[Document]:
    """
    Walk the data directory and build Documents with metadata.
    Recognized files:
      - resume.pdf (type=resume)
      - *.yaml/yml (type inferred by filename: qna/profile/timeline/links/etc., fallback 'profile')
      - *.json (profile-like structured facts)
      - *.md (notes/projects with optional frontmatter)
      - *.txt (notes)
    """
    data_dir = Path(data_dir)
    if not data_dir.exists():
        return []

    docs: List[Document] = []

    for path in data_dir.rglob("*"):
        if path.is_dir():
            continue

        suffix = path.suffix.lower()
        name = path.stem.lower()

        try:
            if suffix == ".pdf":
                text = load_pdf_text(path)
                if text:
                    docs.append(
                        Document(
                            page_content=text,
                            metadata={"source": str(path), "type": "resume" if name == "resume" else "pdf", "filename": path.name},
                        )
                    )
            elif suffix in (".yaml", ".yml"):
                type_hint = (
                    "qna"
                    if "qna" in name
                    else "timeline"
                    if "timeline" in name
                    else "profile"
                    if "profile" in name
                    else "links"
                    if "links" in name
                    else "profile"
                )
                items = load_yaml_facts(path, default_type=type_hint)
                docs.extend(to_documents(items))
            elif suffix == ".json":
                items = load_json_facts(path, default_type="profile")
                docs.extend(to_documents(items))
            elif suffix == ".md":
                docs.append(to_documents([load_md(path, default_type="notes")])[0])
            elif suffix == ".txt":
                docs.append(to_documents([load_txt(path, default_type="notes")])[0])
            else:
                # Ignore other types for now
                pass
        except Exception as e:
            print(f"[loaders] Skipped {path} due to error: {e}")

    return docs
