import re
import sys
import argparse
from pathlib import Path

TOC_START = "<!--TOC-->"
TOC_END = "<!--TOCSTOP-->"


def github_anchor(header: str) -> str:
    anchor = header.lower()
    anchor = re.sub(r"[^\w\s-]", "", anchor)  # remove punctuation
    anchor = re.sub(r"\s+", "-", anchor)      # spaces to dashes
    return anchor.strip("-")


def extract_headers(lines, max_depth, skip_first=True):
    headers = []
    for line in lines:
        # Match optional list marker before header (e.g. "- ### Header")
        match = re.match(r"^\s*(?:[-*+]\s+)?(#{1,6})\s+(.*)", line)
        if match:
            level = len(match.group(1))
            text = match.group(2).strip()
            if text and level <= max_depth:
                headers.append((level, text))

    if skip_first and headers:
        return headers[1:]  # skip the first heading
    return headers


def build_toc(headers):
    toc_lines = []
    for level, text in headers:
        indent = "  " * (level - 1)
        anchor = github_anchor(text)
        toc_lines.append(f"{indent}- [{text}](#{anchor})")
    return toc_lines


def inject_toc(lines, toc_lines):
    toc_block = [TOC_START, ""] + toc_lines + ["", TOC_END]
    start_idx = end_idx = None

    for i, line in enumerate(lines):
        if TOC_START in line:
            start_idx = i
        if TOC_END in line:
            end_idx = i

    if start_idx is None or end_idx is None or end_idx <= start_idx:
        print("Error: Missing or malformed TOC markers (<!--TOC--> and <!--TOCSTOP-->)")
        sys.exit(1)

    return lines[:start_idx] + toc_block + lines[end_idx + 1:]


def main():
    parser = argparse.ArgumentParser(
        description="Generate a GitHub-compatible TOC for a Markdown file."
    )
    parser.add_argument("input", help="Path to input Markdown file")
    group = parser.add_mutually_exclusive_group()
    group.add_argument("--output", help="Write result to a new file (default is in-place)")
    parser.add_argument("--depth", type=int, default=6, help="Max heading depth (1–6, default: 6)")
    parser.add_argument("--include-first-header", dest="include_first", action="store_true",
                        help="Include the first top-level header in the TOC")
    parser.add_argument("--no-include-first-header", dest="include_first", action="store_false",
                        help="Exclude the first header (default)")
    parser.set_defaults(include_first=False)

    args = parser.parse_args()

    input_path = Path(args.input)
    lines = input_path.read_text(encoding="utf-8").splitlines()

    headers = extract_headers(lines, args.depth, skip_first=not args.include_first)
    toc_lines = build_toc(headers)
    new_lines = inject_toc(lines, toc_lines)
    new_content = "\n".join(new_lines) + "\n"

    if args.output:
        Path(args.output).write_text(new_content, encoding="utf-8")
        print(f"TOC written to: {args.output}")
    else:
        input_path.write_text(new_content, encoding="utf-8")
        print(f"TOC updated in-place: {input_path}")


if __name__ == "__main__":
    main()
