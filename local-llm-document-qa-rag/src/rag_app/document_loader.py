from __future__ import annotations

from pathlib import Path
from typing import Iterable

from .models import Document

SUPPORTED_EXTENSIONS = {".md", ".txt", ".text", ".pdf"}


def iter_document_paths(root: str | Path) -> Iterable[Path]:
    """Yield supported document paths under a file or directory."""
    root_path = Path(root)
    if root_path.is_file():
        if root_path.suffix.lower() in SUPPORTED_EXTENSIONS:
            yield root_path
        return
    for path in sorted(root_path.rglob("*")):
        if path.is_file() and path.suffix.lower() in SUPPORTED_EXTENSIONS:
            yield path


def _read_pdf(path: Path) -> str:
    try:
        from pypdf import PdfReader  # type: ignore
    except Exception as exc:  # pragma: no cover - optional dependency path
        raise RuntimeError(
            f"PDF support requires the optional pypdf dependency. Install with: pip install -e '.[full]'"
        ) from exc

    reader = PdfReader(str(path))
    parts: list[str] = []
    for index, page in enumerate(reader.pages, start=1):
        text = page.extract_text() or ""
        parts.append(f"\n[page {index}]\n{text}")
    return "\n".join(parts).strip()


def load_document(path: str | Path, base_dir: str | Path | None = None) -> Document:
    """Load a document from disk and normalize its source name."""
    file_path = Path(path)
    suffix = file_path.suffix.lower()
    if suffix == ".pdf":
        text = _read_pdf(file_path)
    else:
        text = file_path.read_text(encoding="utf-8", errors="replace")

    if base_dir is not None:
        try:
            source = str(file_path.relative_to(Path(base_dir)))
        except ValueError:
            source = file_path.name
    else:
        source = file_path.name

    return Document(
        source=source.replace("\\", "/"),
        text=text,
        metadata={"path": str(file_path), "extension": suffix},
    )


def load_documents(root: str | Path) -> list[Document]:
    """Load all supported documents under root."""
    root_path = Path(root)
    return [load_document(path, root_path if root_path.is_dir() else path.parent) for path in iter_document_paths(root_path)]
