from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
import re

CHUNKER_VERSION = "2.0"

_REQUIREMENT_LINE = re.compile(
    r"^\s*-\s+\*\*([TF]\d+)\*\*\s+[—-]\s+(.+?)\s*$",
    re.IGNORECASE,
)
_HEADING = re.compile(r"^(#{1,6})\s+(.+?)\s*$")


@dataclass(frozen=True)
class Chunk:
    id: str
    text: str
    source: str
    section: str
    requirement_ids: tuple[str, ...]


def _slug(value: str) -> str:
    value = re.sub(r"[^a-zA-Z0-9]+", "-", value.strip()).strip("-").lower()
    return value[:90] or "section"


class MarkdownSectionChunker:
    """Create retrieval-friendly chunks from the Markdown knowledge base.

    Product requirements (T*/F*) are emitted as atomic chunks so retrieval can
    be evaluated against a precise requirement ID. Non-requirement prose is
    chunked by heading/paragraph.

    Training/evaluation sections are excluded as a defence-in-depth measure.
    They should not live in the knowledge base, but if somebody accidentally
    adds them later they still won't be indexed.
    """

    SKIPPED_SECTION_TITLES = {"Suggested RAG Test Questions"}

    def __init__(self, max_chars: int = 1800, overlap_chars: int = 180):
        if max_chars < 200:
            raise ValueError("max_chars must be at least 200")
        if overlap_chars < 0 or overlap_chars >= max_chars:
            raise ValueError("overlap_chars must be >= 0 and smaller than max_chars")
        self.max_chars = max_chars
        self.overlap_chars = overlap_chars

    def load(self, path: Path) -> list[Chunk]:
        text = path.read_text(encoding="utf-8")
        return self.chunk(text=text, source=path.name)

    def chunk(self, text: str, source: str = "requirements.md") -> list[Chunk]:
        sections = self._parse_sections(text)
        chunks: list[Chunk] = []
        generic_counter = 0

        for section_path, lines in sections:
            requirement_lines: list[tuple[str, str]] = []
            prose_lines: list[str] = []

            for line in lines:
                match = _REQUIREMENT_LINE.match(line)
                if match:
                    requirement_lines.append((match.group(1).upper(), match.group(2).strip()))
                else:
                    prose_lines.append(line)

            leaf = section_path.split(" > ")[-1]
            for requirement_id, requirement_text in requirement_lines:
                chunks.append(
                    Chunk(
                        id=f"{requirement_id.lower()}-{_slug(leaf)}",
                        text=(
                            f"Section: {section_path}\n"
                            f"Requirement {requirement_id}: {requirement_text}"
                        ),
                        source=source,
                        section=section_path,
                        requirement_ids=(requirement_id,),
                    )
                )

            prose = self._clean_prose(prose_lines)
            if prose:
                for part in self._split_long(f"Section: {section_path}\n\n{prose}"):
                    generic_counter += 1
                    ids = tuple(dict.fromkeys(re.findall(r"\b[TF]\d+\b", part)))
                    chunks.append(
                        Chunk(
                            id=f"{_slug(section_path)}-{generic_counter:03d}",
                            text=part,
                            source=source,
                            section=section_path,
                            requirement_ids=ids,
                        )
                    )

        return chunks

    def _parse_sections(self, text: str) -> list[tuple[str, list[str]]]:
        sections: list[tuple[str, list[str]]] = []
        heading_stack: list[tuple[int, str]] = []
        current_path = "Document Overview"
        current_lines: list[str] = []
        skip_level: int | None = None

        def flush() -> None:
            nonlocal current_lines
            if current_lines:
                sections.append((current_path, current_lines))
                current_lines = []

        for line in text.splitlines():
            heading_match = _HEADING.match(line)
            if heading_match:
                level = len(heading_match.group(1))
                title = heading_match.group(2).strip()

                # If we are skipping a subtree, only a heading at the same or a
                # higher level can end that subtree.
                if skip_level is not None:
                    if level > skip_level:
                        continue
                    skip_level = None

                flush()

                heading_stack = [(lvl, name) for lvl, name in heading_stack if lvl < level]
                heading_stack.append((level, title))
                current_path = " > ".join(name for _, name in heading_stack)

                if title in self.SKIPPED_SECTION_TITLES:
                    skip_level = level
                    current_lines = []
                continue

            if skip_level is None:
                current_lines.append(line)

        flush()
        return sections

    @staticmethod
    def _clean_prose(lines: list[str]) -> str:
        # Remove separators and collapse excessive blank lines while preserving
        # Markdown bullets/quotes that carry source content.
        cleaned: list[str] = []
        blank = False
        for raw in lines:
            line = raw.rstrip()
            if line.strip() == "---":
                continue
            if not line.strip():
                if cleaned and not blank:
                    cleaned.append("")
                blank = True
                continue
            cleaned.append(line)
            blank = False
        return "\n".join(cleaned).strip()

    def _split_long(self, text: str) -> list[str]:
        if len(text) <= self.max_chars:
            return [text]

        paragraphs = [p.strip() for p in text.split("\n\n") if p.strip()]
        parts: list[str] = []
        current = ""
        for paragraph in paragraphs:
            candidate = f"{current}\n\n{paragraph}".strip()
            if current and len(candidate) > self.max_chars:
                parts.append(current)
                overlap = current[-self.overlap_chars :] if self.overlap_chars else ""
                current = f"{overlap}\n\n{paragraph}".strip()
            else:
                current = candidate
        if current:
            parts.append(current)
        return parts
