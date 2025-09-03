from __future__ import annotations

import re
import sys
from pathlib import Path
from typing import Tuple


TOKEN_LINE_RE = re.compile(
	r"Input tokens:\s*([\d,]+)\s*\|\s*Output tokens:\s*([\d,]+)\s*\|\s*Total tokens:\s*([\d,]+)",
	re.IGNORECASE,
)


def parse_token_line(text: str) -> Tuple[int, int, int] | None:
	"""Find and parse the token counts from the provided markdown text.

	Returns a tuple (input_tokens, output_tokens, total_tokens) or None if not found.
	"""
	m = TOKEN_LINE_RE.search(text)
	if not m:
		return None
	def to_int(s: str) -> int:
		return int(s.replace(",", "").strip())
	return to_int(m.group(1)), to_int(m.group(2)), to_int(m.group(3))


def human(n: int) -> str:
	return f"{n:,}"


def main(argv: list[str]) -> int:
	# Determine directory to scan: default to the folder containing this script
	if len(argv) > 1:
		base = Path(argv[1]).expanduser().resolve()
	else:
		base = Path(__file__).parent

	if not base.exists() or not base.is_dir():
		print(f"Folder not found or not a directory: {base}", file=sys.stderr)
		return 2

	md_files = sorted(p for p in base.glob("*.md"))
	if not md_files:
		print(f"No markdown files found in: {base}")
		return 0

	total_in = 0
	total_out = 0
	total_all = 0
	parsed = 0
	missing = []

	for p in md_files:
		try:
			text = p.read_text(encoding="utf-8", errors="ignore")
		except Exception as e:
			print(f"WARN: Could not read {p.name}: {e}", file=sys.stderr)
			continue

		res = parse_token_line(text)
		if not res:
			missing.append(p.name)
			continue

		ipt, opt, tot = res
		total_in += ipt
		total_out += opt
		total_all += tot
		parsed += 1

	print(f"Scanned folder: {base}")
	print(f"Files found: {len(md_files)} | Parsed: {parsed} | Missing footer: {len(missing)}")
	if missing:
		# Keep it short; list up to 10
		sample = ", ".join(missing[:10])
		more = f" (+{len(missing) - 10} more)" if len(missing) > 10 else ""
		print(f"Missing in: {sample}{more}")

	print()
	print("Totals across parsed files:")
	print(f"- Input tokens:  {human(total_in)}")
	print(f"- Output tokens: {human(total_out)}")
	print(f"- Total tokens:  {human(total_all)}")

	return 0


if __name__ == "__main__":
	raise SystemExit(main(sys.argv))

