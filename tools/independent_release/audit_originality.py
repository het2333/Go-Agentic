#!/usr/bin/env python3
"""Deterministic, read-only originality audit for the independent release."""

from __future__ import annotations

import argparse
from dataclasses import asdict, dataclass
import fnmatch
import hashlib
import html
from html.parser import HTMLParser
import json
from pathlib import Path
import re
from difflib import SequenceMatcher
import subprocess
import sys
from typing import Iterable, Sequence
from urllib.parse import unquote, urlsplit


IMAGE_SUFFIXES = {".gif", ".jpeg", ".jpg", ".png", ".svg", ".webp"}
LEGACY_PUBLICATION_PATHS = {
    "docs/chapter16/Chapter16-Graduation-Project.md",
    "docs/chapter16/第十六章 毕业设计.md",
}
DEFAULT_REPORT_JSON = Path("docs/independent-release/originality-report.json")
DEFAULT_REPORT_MARKDOWN = Path("docs/independent-release/originality-report.md")
NORMALIZED_FRAGMENT_CHARS = 32

_FENCE_RE = re.compile(r"^\s*(`{3,}|~{3,})")
_INLINE_CODE_RE = re.compile(r"(`+)(.+?)\1")
_IMAGE_RE = re.compile(r"!\[[^\]]*\]\(([^)]+)\)")
_LINK_RE = re.compile(r"\[([^\]]+)\]\([^)]+\)")
_REFERENCE_LINK_RE = re.compile(r"\[([^\]]+)\]\[[^\]]*\]")
_AUTOLINK_RE = re.compile(r"<https?://[^>]+>", re.IGNORECASE)
_URL_RE = re.compile(r"(?:https?://|www\.)[^\s<>)\]]+", re.IGNORECASE)
_HTML_TAG_RE = re.compile(r"<[^>]+>")
_HTML_COMMENT_RE = re.compile(r"<!--.*?-->", re.DOTALL)
_HEADING_RE = re.compile(r"^\s{0,3}#{1,6}\s+(.+?)\s*#*\s*$")
_ORDERED_ITEM_RE = re.compile(r"^\s*\d+[.)]\s+(.+)$")
_UNORDERED_ITEM_RE = re.compile(r"^\s*[-+*]\s+(.+)$")
_SENTENCE_RE = re.compile(r"[^.!?。！？；;]+(?:[.!?。！？；;]+|$)")
_CJK_RE = re.compile(r"[\u3400-\u4dbf\u4e00-\u9fff]+")
_ENGLISH_WORD_RE = re.compile(r"[A-Za-z]+(?:['’-][A-Za-z]+)*")
_MARKDOWN_PUNCTUATION_RE = re.compile(r"[\\`*_{}\[\]()<>#+\-=|~:;,，。！？；：、“”‘’…·.!?]")


class _HTMLImageParser(HTMLParser):
    def __init__(self) -> None:
        super().__init__(convert_charrefs=True)
        self.sources: list[str] = []

    def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        if tag.casefold() != "img":
            return
        for name, value in attrs:
            if name.casefold() == "src" and value is not None:
                self.sources.append(value)
                return


@dataclass(frozen=True)
class AuditFinding:
    kind: str
    current_path: str
    upstream_path: str
    excerpt: str
    location: str


@dataclass(frozen=True)
class _Segment:
    text: str
    line: int


def _strip_non_prose(text: str) -> list[tuple[int, str]]:
    """Return source lines with code, URLs, and Markdown wrappers removed."""
    text = _HTML_COMMENT_RE.sub(
        lambda match: "\n" * match.group(0).count("\n"),
        text,
    )
    lines: list[tuple[int, str]] = []
    fence_char = ""
    fence_size = 0

    for line_number, raw_line in enumerate(text.splitlines(), start=1):
        fence = _FENCE_RE.match(raw_line)
        if fence:
            marker = fence.group(1)
            if not fence_char:
                fence_char = marker[0]
                fence_size = len(marker)
            elif marker[0] == fence_char and len(marker) >= fence_size:
                fence_char = ""
                fence_size = 0
            continue
        if fence_char:
            continue

        line = _INLINE_CODE_RE.sub(" ", raw_line)
        line = _IMAGE_RE.sub(" ", line)
        line = _LINK_RE.sub(r"\1", line)
        line = _REFERENCE_LINK_RE.sub(r"\1", line)
        line = _AUTOLINK_RE.sub(" ", line)
        line = _URL_RE.sub(" ", line)
        line = _HTML_TAG_RE.sub(" ", line)
        line = html.unescape(line)
        line = re.sub(r"^\s{0,3}#{1,6}\s*", "", line)
        line = re.sub(r"^\s*(?:>|[-+*]|\d+[.)])\s+", "", line)
        line = re.sub(r"[*_~|]", "", line)
        line = re.sub(r"\s+", " ", line).strip()
        if line:
            lines.append((line_number, line))
    return lines


def normalize_markdown(text: str) -> str:
    """Normalize prose while preserving line and sentence boundaries."""
    normalized: list[str] = []
    for _, line in _strip_non_prose(text):
        line = _MARKDOWN_PUNCTUATION_RE.sub(" ", line)
        line = re.sub(r"\s+", " ", line).strip().casefold()
        if line:
            normalized.append(line)
    return "\n".join(normalized)


def _sentences(text: str) -> list[_Segment]:
    segments: list[_Segment] = []
    for line_number, line in _strip_non_prose(text):
        for match in _SENTENCE_RE.finditer(line):
            sentence = match.group(0).strip()
            if sentence:
                segments.append(_Segment(sentence, line_number))
    return segments


def _chinese_run(text: str) -> str:
    return "".join(_CJK_RE.findall(text))


def _english_words(text: str) -> tuple[str, ...]:
    return tuple(word.casefold().replace("’", "'") for word in _ENGLISH_WORD_RE.findall(text))


def _chinese_runs(text: str) -> list[str]:
    runs: list[str] = []
    current: list[str] = []
    for character in text:
        if "\u3400" <= character <= "\u4dbf" or "\u4e00" <= character <= "\u9fff":
            current.append(character)
        elif character.isalpha():
            if current:
                runs.append("".join(current))
                current = []
    if current:
        runs.append("".join(current))
    return runs


def _english_word_runs(text: str) -> list[tuple[str, ...]]:
    runs: list[tuple[str, ...]] = []
    current: list[str] = []
    for match in re.finditer(
        r"[A-Za-z]+(?:['’-][A-Za-z]+)*|[^\W\d_A-Za-z]+",
        text,
        re.UNICODE,
    ):
        token = match.group(0)
        if _ENGLISH_WORD_RE.fullmatch(token):
            current.append(token.casefold().replace("’", "'"))
        elif current:
            runs.append(tuple(current))
            current = []
    if current:
        runs.append(tuple(current))
    return runs


def chinese_ngrams(text: str, size: int = 20) -> set[str]:
    if size < 1:
        raise ValueError("Chinese n-gram size must be positive")
    grams: set[str] = set()
    for sentence in _sentences(text):
        for run in _chinese_runs(sentence.text):
            grams.update(run[index:index + size] for index in range(len(run) - size + 1))
    return grams


def english_ngrams(text: str, size: int = 12) -> set[tuple[str, ...]]:
    if size < 1:
        raise ValueError("English n-gram size must be positive")
    grams: set[tuple[str, ...]] = set()
    for sentence in _sentences(text):
        for words in _english_word_runs(sentence.text):
            grams.update(words[index:index + size] for index in range(len(words) - size + 1))
    return grams


def _exact_sentence_key(text: str) -> str:
    terminal_removed = re.sub(r"[.!?。！？；;]+$", "", text.strip())
    return re.sub(r"\s+", " ", terminal_removed).casefold()


def _is_meaningful_sentence(text: str) -> bool:
    return len(_chinese_run(text)) >= 8 or len(_english_words(text)) >= 4


def _normalized_fragment(text: str) -> str:
    return "".join(character.casefold() for character in text if character.isalnum())


def _maximal_matching_blocks(
    current: Sequence[str] | str,
    upstream: Sequence[str] | str,
    minimum: int,
) -> Iterable[tuple[int, int, int]]:
    if len(current) < minimum or len(upstream) < minimum:
        return ()
    return (
        (block.a, block.b, block.size)
        for block in SequenceMatcher(None, current, upstream, autojunk=False).get_matching_blocks()
        if block.size >= minimum
    )


def _candidate_index(values: Sequence[Sequence[str] | str], size: int) -> dict[object, set[int]]:
    index: dict[object, set[int]] = {}
    for value_index, value in enumerate(values):
        for start in range(len(value) - size + 1):
            key = value[start:start + size]
            index.setdefault(key, set()).add(value_index)
    return index


def _candidate_ids(
    value: Sequence[str] | str,
    size: int,
    index: dict[object, set[int]],
) -> set[int]:
    candidates: set[int] = set()
    for start in range(len(value) - size + 1):
        candidates.update(index.get(value[start:start + size], ()))
    return candidates


def _content_tokens(text: str) -> set[str]:
    tokens = set(_english_words(text))
    for run in _CJK_RE.findall(text):
        if len(run) == 1:
            tokens.add(run)
        else:
            tokens.update(run[index:index + 2] for index in range(len(run) - 1))
    return tokens


def _jaccard(left: set[str], right: set[str]) -> float:
    return len(left & right) / len(left | right) if left and right else 0.0


def _ordered_paragraph_similarity(
    current: Sequence[set[str]], upstream: Sequence[set[str]]
) -> tuple[bool, float]:
    candidates = sorted(
        (
            (_jaccard(current_tokens, upstream_tokens), current_index, upstream_index)
            for current_index, current_tokens in enumerate(current)
            for upstream_index, upstream_tokens in enumerate(upstream)
        ),
        key=lambda item: (-item[0], item[1], item[2]),
    )
    used_current: set[int] = set()
    used_upstream: set[int] = set()
    matches: list[tuple[int, int]] = []
    for score, current_index, upstream_index in candidates:
        if score < 0.3:
            break
        if current_index in used_current or upstream_index in used_upstream:
            continue
        used_current.add(current_index)
        used_upstream.add(upstream_index)
        matches.append((current_index, upstream_index))

    matches.sort()
    if len(matches) < 4 or len(matches) / min(len(current), len(upstream)) < 0.6:
        return False, 0.0
    upstream_order = [upstream_index for _, upstream_index in matches]
    increasing_pairs = sum(
        left < right for left, right in zip(upstream_order, upstream_order[1:])
    )
    order_ratio = increasing_pairs / max(1, len(upstream_order) - 1)
    return order_ratio >= 0.8, order_ratio


def _structure_fingerprint(text: str) -> tuple[list[str], list[set[str]], list[set[str]]]:
    headings: list[str] = []
    ordered_steps: list[set[str]] = []
    paragraphs: list[set[str]] = []
    in_fence = False
    fence_char = ""
    fence_size = 0

    for raw_line in text.splitlines():
        fence = _FENCE_RE.match(raw_line)
        if fence:
            marker = fence.group(1)
            if not in_fence:
                in_fence = True
                fence_char = marker[0]
                fence_size = len(marker)
            elif marker[0] == fence_char and len(marker) >= fence_size:
                in_fence = False
            continue
        if in_fence or not raw_line.strip():
            continue
        heading = _HEADING_RE.match(raw_line)
        if heading:
            key = _normalized_fragment(_strip_non_prose(heading.group(1))[0][1]) if _strip_non_prose(heading.group(1)) else ""
            if key:
                headings.append(key)
        elif ordered_item := _ORDERED_ITEM_RE.match(raw_line):
            cleaned = _strip_non_prose(ordered_item.group(1))
            if cleaned:
                tokens = _content_tokens(cleaned[0][1])
                if tokens:
                    ordered_steps.append(tokens)
        elif _UNORDERED_ITEM_RE.match(raw_line):
            continue
        elif raw_line.lstrip().startswith(">"):
            continue
        else:
            cleaned = _strip_non_prose(raw_line)
            if cleaned:
                tokens = _content_tokens(cleaned[0][1])
                if len(tokens) >= 3:
                    paragraphs.append(tokens)
    return headings, ordered_steps, paragraphs


def _audit_text_with_paths(
    current: str,
    upstream: str,
    zh_chars: int,
    en_words: int,
    current_path: str,
    upstream_path: str,
) -> list[AuditFinding]:
    current_sentences = _sentences(current)
    upstream_sentences = _sentences(upstream)
    findings: set[AuditFinding] = set()

    upstream_exact = {
        _exact_sentence_key(segment.text)
        for segment in upstream_sentences
        if _is_meaningful_sentence(segment.text)
    }
    exact_keys: set[str] = set()
    for segment in current_sentences:
        key = _exact_sentence_key(segment.text)
        has_terminal = bool(re.search(r"[.!?。！？；;]+$", segment.text))
        if has_terminal and _is_meaningful_sentence(segment.text) and key in upstream_exact:
            excerpt = re.sub(r"[.!?。！？；;]+$", "", segment.text).strip()
            findings.add(AuditFinding(
                "exact_sentence", current_path, upstream_path, excerpt, f"line {segment.line}"
            ))
            exact_keys.add(_normalized_fragment(segment.text))

    upstream_chinese = [
        run for segment in upstream_sentences for run in _chinese_runs(segment.text)
    ]
    chinese_index = _candidate_index(upstream_chinese, zh_chars)
    for current_segment in current_sentences:
        for current_run in _chinese_runs(current_segment.text):
            for upstream_index in _candidate_ids(current_run, zh_chars, chinese_index):
                upstream_run = upstream_chinese[upstream_index]
                for start, _, size in _maximal_matching_blocks(current_run, upstream_run, zh_chars):
                    excerpt = current_run[start:start + size]
                    if _normalized_fragment(excerpt) in exact_keys:
                        continue
                    findings.add(AuditFinding(
                        "chinese_run", current_path, upstream_path, excerpt, f"line {current_segment.line}"
                    ))

    upstream_english = [
        run for segment in upstream_sentences for run in _english_word_runs(segment.text)
    ]
    english_index = _candidate_index(upstream_english, en_words)
    for current_segment in current_sentences:
        for current_words in _english_word_runs(current_segment.text):
            for upstream_index in _candidate_ids(current_words, en_words, english_index):
                upstream_words = upstream_english[upstream_index]
                for start, _, size in _maximal_matching_blocks(current_words, upstream_words, en_words):
                    excerpt = " ".join(current_words[start:start + size])
                    if _normalized_fragment(excerpt) in exact_keys:
                        continue
                    findings.add(AuditFinding(
                        "english_run", current_path, upstream_path, excerpt, f"line {current_segment.line}"
                    ))

    existing_normalized = {_normalized_fragment(item.excerpt) for item in findings}
    upstream_fragments = [_normalized_fragment(segment.text) for segment in upstream_sentences]
    fragment_index = _candidate_index(upstream_fragments, NORMALIZED_FRAGMENT_CHARS)
    for current_segment in current_sentences:
        current_fragment = _normalized_fragment(current_segment.text)
        for upstream_index in _candidate_ids(
            current_fragment, NORMALIZED_FRAGMENT_CHARS, fragment_index
        ):
            upstream_fragment = upstream_fragments[upstream_index]
            for start, _, size in _maximal_matching_blocks(
                current_fragment,
                upstream_fragment,
                NORMALIZED_FRAGMENT_CHARS,
            ):
                excerpt = current_fragment[start:start + size]
                if any(excerpt in prior or prior in excerpt for prior in existing_normalized if prior):
                    continue
                findings.add(AuditFinding(
                    "normalized_fragment", current_path, upstream_path, excerpt, f"line {current_segment.line}"
                ))

    current_headings, current_steps, current_paragraphs = _structure_fingerprint(current)
    upstream_headings, upstream_steps, upstream_paragraphs = _structure_fingerprint(upstream)
    heading_ratio = (
        SequenceMatcher(None, current_headings, upstream_headings, autojunk=False).ratio()
        if current_headings and upstream_headings else 0.0
    )
    step_scores = [
        _jaccard(current_tokens, upstream_tokens)
        for current_tokens, upstream_tokens in zip(current_steps, upstream_steps)
    ]
    step_ratio = (
        sum(step_scores) / len(step_scores)
        if min(len(current_steps), len(upstream_steps)) >= 3
        and abs(len(current_steps) - len(upstream_steps)) <= 1
        else 0.0
    )
    paragraph_match, paragraph_order_ratio = _ordered_paragraph_similarity(
        current_paragraphs, upstream_paragraphs
    )
    structurally_similar = (
        (min(len(current_headings), len(upstream_headings)) >= 2 and heading_ratio >= 0.8)
        or step_ratio >= 0.5
        or paragraph_match
    )
    if structurally_similar:
        if min(len(current_headings), len(upstream_headings)) >= 2 and heading_ratio >= 0.8:
            excerpt = "headings: " + " > ".join(current_headings[:8])
        elif step_ratio >= 0.5:
            excerpt = f"ordered-step-similarity:{step_ratio:.2f}"
        else:
            excerpt = f"paragraph-order-similarity:{paragraph_order_ratio:.2f}"
        findings.add(AuditFinding(
            "structural_similarity", current_path, upstream_path, excerpt, "document structure"
        ))

    return sorted(findings, key=_finding_key)


def audit_text(
    current: str,
    upstream: str,
    zh_chars: int = 20,
    en_words: int = 12,
) -> list[AuditFinding]:
    return _audit_text_with_paths(current, upstream, zh_chars, en_words, "", "")


def validate_allowlist(allowlist: list[dict]) -> list[dict]:
    required = {"current_path", "excerpt", "reason"}
    validated: list[dict] = []
    for index, entry in enumerate(allowlist):
        if not isinstance(entry, dict) or not required.issubset(entry):
            raise ValueError(
                f"Allowlist entry {index} must contain current_path, excerpt, and reason"
            )
        if any(not isinstance(entry[field], str) or not entry[field].strip() for field in required):
            raise ValueError(
                f"Allowlist entry {index} must contain non-empty current_path, excerpt, and reason"
            )
        if any(character in entry["current_path"] for character in "*?["):
            raise ValueError(f"Allowlist entry {index} must use a literal current_path")
        validated.append({field: entry[field] for field in ("current_path", "excerpt", "reason")})
    return validated


def _is_allowed(finding: AuditFinding, allowlist: list[dict]) -> bool:
    return any(
        entry["current_path"] == finding.current_path
        and entry["excerpt"] == finding.excerpt
        for entry in allowlist
    )


def audit_markdown(
    current: str,
    upstream: str,
    allowlist: list[dict],
    current_path: str = "",
    upstream_path: str = "",
    zh_chars: int = 20,
    en_words: int = 12,
) -> list[AuditFinding]:
    validated = validate_allowlist(allowlist)
    upstream_path = upstream_path or current_path
    findings = _audit_text_with_paths(
        current, upstream, zh_chars, en_words, current_path, upstream_path
    )
    return [finding for finding in findings if not _is_allowed(finding, validated)]


def publication_markdown_paths(root: Path) -> list[str]:
    root = root.resolve()
    paths: list[str] = []
    for relative in (
        "README.md",
        "README_EN.md",
        "docs/README.md",
        "docs/README_EN.md",
        "docs/前言.md",
        "docs/Preface.md",
    ):
        if (root / relative).is_file():
            paths.append(relative)

    for chapter_number in range(1, 26):
        directory = root / "docs" / f"chapter{chapter_number}"
        if not directory.is_dir():
            continue
        chapter_paths = [
            path.relative_to(root).as_posix()
            for path in sorted(directory.glob("*.md"))
            if path.relative_to(root).as_posix() not in LEGACY_PUBLICATION_PATHS
        ]
        english = [path for path in chapter_paths if Path(path).name.startswith("Chapter")]
        chinese = [path for path in chapter_paths if not Path(path).name.startswith("Chapter")]
        paths.extend(english[:1])
        paths.extend(chinese[:1])

    appendices = root / "docs" / "appendices"
    if appendices.is_dir():
        paths.extend(path.relative_to(root).as_posix() for path in sorted(appendices.glob("*.md")))
    return sorted(dict.fromkeys(paths))


def _matches(path: str, includes: Sequence[str] | None) -> bool:
    return not includes or any(fnmatch.fnmatchcase(path, pattern) for pattern in includes)


def _current_markdown_paths(root: Path, includes: Sequence[str] | None) -> list[str]:
    if not includes:
        return publication_markdown_paths(root)
    return sorted(
        path.relative_to(root).as_posix()
        for path in root.rglob("*.md")
        if ".git" not in path.parts
        and path.relative_to(root).as_posix() not in LEGACY_PUBLICATION_PATHS
        and _matches(path.relative_to(root).as_posix(), includes)
    )


def _git_bytes(root: Path, ref: str, relative_path: str) -> bytes | None:
    result = subprocess.run(
        ["git", "show", f"{ref}:{relative_path}"],
        cwd=root,
        capture_output=True,
    )
    if result.returncode == 0:
        return result.stdout
    missing_markers = (b"does not exist in", b"exists on disk, but not in", b"Path '")
    if any(marker in result.stderr for marker in missing_markers):
        return None
    raise RuntimeError(result.stderr.decode("utf-8", errors="replace").strip())


def _git_paths(root: Path, ref: str, prefix: str = "") -> list[str]:
    command = ["git", "ls-tree", "-r", "-z", "--name-only", ref]
    if prefix:
        command.extend(["--", prefix])
    result = subprocess.run(command, cwd=root, check=True, capture_output=True)
    return sorted(path.decode("utf-8") for path in result.stdout.split(b"\0") if path)


def _local_image_candidate(root: Path, markdown_path: Path, raw_target: str) -> Path | None:
    target = unquote(html.unescape(raw_target.strip().strip("<>")))
    parsed = urlsplit(target)
    if not target or parsed.scheme or parsed.netloc:
        return None
    local_path = parsed.path
    if not local_path:
        return None
    candidate = root / "docs" / local_path.lstrip("/") if local_path.startswith("/") else markdown_path.parent / local_path
    try:
        candidate = candidate.resolve()
        candidate.relative_to(root)
    except ValueError:
        return None
    if candidate.is_file() and candidate.suffix.casefold() in IMAGE_SUFFIXES:
        return candidate
    return None


def _local_image_paths(root: Path, markdown_paths: Sequence[str]) -> list[str]:
    images: set[str] = set()
    for relative_path in markdown_paths:
        markdown_path = root / relative_path
        text = markdown_path.read_text(encoding="utf-8")
        targets = [match.group(1).strip().split()[0] for match in _IMAGE_RE.finditer(text)]
        html_images = _HTMLImageParser()
        html_images.feed(text)
        targets.extend(html_images.sources)
        for target in targets:
            candidate = _local_image_candidate(root, markdown_path, target)
            if candidate is not None:
                images.add(candidate.relative_to(root).as_posix())
    return sorted(images)


def audit_repository(
    root: Path,
    upstream_ref: str,
    allowlist: list[dict],
    includes: Sequence[str] | None = None,
) -> list[AuditFinding]:
    root = root.resolve()
    validated = validate_allowlist(allowlist)
    markdown_paths = _current_markdown_paths(root, includes)
    findings: list[AuditFinding] = []

    for relative_path in markdown_paths:
        current_bytes = (root / relative_path).read_bytes()
        upstream_bytes = _git_bytes(root, upstream_ref, relative_path)
        if upstream_bytes is None:
            continue
        current_text = current_bytes.decode("utf-8")
        upstream_text = upstream_bytes.decode("utf-8")
        findings.extend(audit_markdown(
            current_text,
            upstream_text,
            validated,
            current_path=relative_path,
            upstream_path=relative_path,
        ))
        if current_bytes == upstream_bytes:
            digest = hashlib.sha256(current_bytes).hexdigest()
            finding = AuditFinding(
                "identical_publication_blob",
                relative_path,
                relative_path,
                f"sha256:{digest}",
                "file",
            )
            if not _is_allowed(finding, validated):
                findings.append(finding)

    linked_images = _local_image_paths(root, markdown_paths)
    if linked_images:
        upstream_image_hashes: dict[str, list[str]] = {}
        for upstream_path in _git_paths(root, upstream_ref, "docs"):
            if Path(upstream_path).suffix.casefold() not in IMAGE_SUFFIXES:
                continue
            content = _git_bytes(root, upstream_ref, upstream_path)
            if content is None:
                continue
            digest = hashlib.sha256(content).hexdigest()
            upstream_image_hashes.setdefault(digest, []).append(upstream_path)

        for relative_path in linked_images:
            digest = hashlib.sha256((root / relative_path).read_bytes()).hexdigest()
            for upstream_path in upstream_image_hashes.get(digest, []):
                finding = AuditFinding(
                    "image_sha256",
                    relative_path,
                    upstream_path,
                    f"sha256:{digest}",
                    "file",
                )
                if not _is_allowed(finding, validated):
                    findings.append(finding)

    return sorted(set(findings), key=_finding_key)


def _finding_key(finding: AuditFinding) -> tuple[str, str, str, str, str]:
    return (
        finding.current_path,
        finding.location,
        finding.kind,
        finding.upstream_path,
        finding.excerpt,
    )


def _review_rows(
    markdown_paths: Sequence[str],
    findings: Sequence[AuditFinding],
    previous: dict[str, dict] | None = None,
) -> dict[str, dict]:
    previous = previous or {}
    counts: dict[str, int] = {}
    for finding in findings:
        if finding.current_path.endswith(".md"):
            counts[finding.current_path] = counts.get(finding.current_path, 0) + 1

    reviews: dict[str, dict] = {}
    for path in sorted(markdown_paths):
        prior = previous.get(path, {})
        current_count = counts.get(path, 0)
        reviews[path] = {
            "reviewed": bool(prior.get("reviewed", False)),
            "finding_count_before_review": prior.get(
                "finding_count_before_review", current_count
            ),
            "rewritten_sections": list(prior.get("rewritten_sections", [])),
            "reviewed_sections": list(prior.get("reviewed_sections", [])),
            "final_unallowed_count": current_count,
            "review_notes": str(prior.get("review_notes", "")),
        }
    return reviews


def render_json_report(
    findings: Sequence[AuditFinding],
    reviews: dict[str, dict],
    upstream_ref: str,
    includes: Sequence[str] | None,
) -> str:
    unreviewed = [path for path, review in sorted(reviews.items()) if not review.get("reviewed")]
    payload = {
        "schema_version": 1,
        "upstream_ref": upstream_ref,
        "include": list(includes or []),
        "summary": {
            "audited_files": len(reviews),
            "unallowed_findings": len(findings),
            "unreviewed_files": len(unreviewed),
        },
        "findings": [asdict(finding) for finding in sorted(findings, key=_finding_key)],
        "reviews": {path: reviews[path] for path in sorted(reviews)},
    }
    return json.dumps(payload, ensure_ascii=False, indent=2, sort_keys=False) + "\n"


def _markdown_cell(value: object) -> str:
    return str(value).replace("|", "\\|").replace("\n", " ")


def render_markdown_report(
    findings: Sequence[AuditFinding],
    reviews: dict[str, dict],
    upstream_ref: str,
    includes: Sequence[str] | None,
) -> str:
    lines = [
        "# Originality review matrix",
        "",
        f"Upstream reference: `{upstream_ref}`",
        f"Include filters: `{', '.join(includes) if includes else '(publication surface)'}`",
        f"Unallowed findings: **{len(findings)}**",
        "",
        "## Review matrix",
        "",
        "| Current path | Reviewed | Before | Final | Rewritten sections | Reviewed sections | Review notes |",
        "| --- | --- | ---: | ---: | --- | --- | --- |",
    ]
    for path, review in sorted(reviews.items()):
        rewritten_sections = ", ".join(review.get("rewritten_sections", []))
        reviewed_sections = ", ".join(review.get("reviewed_sections", []))
        lines.append(
            f"| {_markdown_cell(path)} | {'yes' if review.get('reviewed') else 'no'} | "
            f"{review.get('finding_count_before_review', 0)} | "
            f"{review.get('final_unallowed_count', 0)} | "
            f"{_markdown_cell(rewritten_sections)} | {_markdown_cell(reviewed_sections)} | "
            f"{_markdown_cell(review.get('review_notes', ''))} |"
        )

    lines.extend([
        "",
        "## Unallowed findings",
        "",
        "| Kind | Current path | Upstream path | Location | Excerpt |",
        "| --- | --- | --- | --- | --- |",
    ])
    for finding in sorted(findings, key=_finding_key):
        lines.append(
            f"| {_markdown_cell(finding.kind)} | {_markdown_cell(finding.current_path)} | "
            f"{_markdown_cell(finding.upstream_path)} | {_markdown_cell(finding.location)} | "
            f"{_markdown_cell(finding.excerpt)} |"
        )
    if not findings:
        lines.append("| — | — | — | — | — |")
    return "\n".join(lines) + "\n"


def _load_allowlist(path: Path) -> list[dict]:
    if not path.is_file():
        raise ValueError(f"Allowlist does not exist: {path}")
    payload = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(payload, list):
        raise ValueError("Allowlist root must be a JSON array")
    return validate_allowlist(payload)


def _load_previous_reviews(path: Path) -> dict[str, dict]:
    if not path.is_file():
        return {}
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except (json.JSONDecodeError, OSError):
        return {}
    reviews = payload.get("reviews", {}) if isinstance(payload, dict) else {}
    return reviews if isinstance(reviews, dict) else {}


def _write_report(path: Path, content: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content, encoding="utf-8")


def build_argument_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--root", type=Path, default=Path("."))
    parser.add_argument("--upstream", default="upstream/main")
    parser.add_argument(
        "--allowlist",
        type=Path,
        default=Path("tools/independent_release/originality_allowlist.json"),
    )
    parser.add_argument(
        "--include",
        action="append",
        default=[],
        help="Repeatable fnmatch-style path pattern.",
    )
    parser.add_argument("--json", type=Path)
    parser.add_argument("--markdown", type=Path)
    parser.add_argument("--require-reviewed", action="store_true")
    return parser


def main(argv: Sequence[str] | None = None) -> int:
    args = build_argument_parser().parse_args(argv)
    root = args.root.resolve()
    allowlist_path = args.allowlist if args.allowlist.is_absolute() else root / args.allowlist
    json_path = args.json
    if json_path is not None and not json_path.is_absolute():
        json_path = root / json_path
    markdown_path = args.markdown
    if markdown_path is not None and not markdown_path.is_absolute():
        markdown_path = root / markdown_path

    try:
        allowlist = _load_allowlist(allowlist_path)
        findings = audit_repository(root, args.upstream, allowlist, includes=args.include)
    except (ValueError, RuntimeError, subprocess.CalledProcessError, UnicodeDecodeError) as error:
        print(f"audit error: {error}", file=sys.stderr)
        return 2

    markdown_paths = _current_markdown_paths(root, args.include)
    canonical_report = root / DEFAULT_REPORT_JSON
    previous_reviews = _load_previous_reviews(canonical_report)
    if json_path == canonical_report:
        previous_reviews = _load_previous_reviews(json_path)
    reviews = _review_rows(markdown_paths, findings, previous_reviews)

    json_content = render_json_report(findings, reviews, args.upstream, args.include)
    markdown_content = render_markdown_report(findings, reviews, args.upstream, args.include)
    if json_path is not None:
        _write_report(json_path, json_content)
    if markdown_path is not None:
        _write_report(markdown_path, markdown_content)

    unreviewed = [path for path, review in reviews.items() if not review["reviewed"]]
    print(
        f"audited {len(markdown_paths)} Markdown files; "
        f"{len(findings)} unallowed findings; {len(unreviewed)} unreviewed"
    )
    if findings or (args.require_reviewed and unreviewed):
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
