from dataclasses import dataclass


DEFAULT_MAX_CHUNK_LINES = 80
DEFAULT_OVERLAP_LINES = 10


@dataclass
class CodeChunk:
    content: str
    start_line: int
    end_line: int


STRUCTURAL_PREFIXES = (
    "def ",
    "async def ",
    "class ",
    "function ",
    "async function ",
    "export function ",
    "export async function ",
    "export class ",
    "interface ",
    "export interface ",
    "type ",
    "export type ",
)


def is_structural_boundary(
    line: str,
) -> bool:
    """
    Return True when a line looks like the beginning of a
    meaningful code structure such as a function or class.
    """

    stripped_line = line.strip()

    return any(
        stripped_line.startswith(prefix)
        for prefix in STRUCTURAL_PREFIXES
    )


def find_preferred_end_index(
    lines: list[str],
    start_index: int,
    proposed_end_index: int,
    minimum_chunk_lines: int,
) -> int:
    """
    Search backwards near the proposed chunk boundary for a
    structural declaration.

    If one is found, end the current chunk immediately before
    that declaration so the next chunk can begin near a logical
    code boundary.
    """

    search_start = (
        start_index + minimum_chunk_lines
    )

    for index in range(
        proposed_end_index - 1,
        search_start - 1,
        -1,
    ):
        if is_structural_boundary(
            lines[index]
        ):
            return index

    return proposed_end_index


def chunk_text_by_lines(
    content: str,
    max_chunk_lines: int = DEFAULT_MAX_CHUNK_LINES,
    overlap_lines: int = DEFAULT_OVERLAP_LINES,
) -> list[CodeChunk]:
    """
    Split text/code into overlapping chunks while preferring
    logical code boundaries when possible.
    """

    if not content.strip():
        return []

    if max_chunk_lines <= 0:
        raise ValueError(
            "max_chunk_lines must be greater than zero."
        )

    if overlap_lines < 0:
        raise ValueError(
            "overlap_lines cannot be negative."
        )

    if overlap_lines >= max_chunk_lines:
        raise ValueError(
            "overlap_lines must be smaller than max_chunk_lines."
        )

    lines = content.splitlines()

    chunks: list[CodeChunk] = []

    start_index = 0

    minimum_chunk_lines = max(
        max_chunk_lines // 2,
        1,
    )

    while start_index < len(lines):
        proposed_end_index = min(
            start_index + max_chunk_lines,
            len(lines),
        )

        if proposed_end_index < len(lines):
            end_index = find_preferred_end_index(
                lines=lines,
                start_index=start_index,
                proposed_end_index=proposed_end_index,
                minimum_chunk_lines=minimum_chunk_lines,
            )
        else:
            end_index = proposed_end_index

        # Safety fallback to guarantee forward progress.
        if end_index <= start_index:
            end_index = proposed_end_index

        chunk_lines = lines[
            start_index:end_index
        ]

        chunk_content = "\n".join(
            chunk_lines
        ).strip()

        if chunk_content:
            chunks.append(
                CodeChunk(
                    content=chunk_content,
                    start_line=start_index + 1,
                    end_line=end_index,
                )
            )

        if end_index >= len(lines):
            break

        next_start_index = max(
            end_index - overlap_lines,
            start_index + 1,
        )

        start_index = next_start_index

    return chunks