# extensions/problemlist.py
import re
import yaml
import os
from pathlib import Path
from markdown.extensions import Extension as MDXExtension
from markdown.preprocessors import Preprocessor as MDXPreprocessor

# Regex for natural sorting (so toi2 comes before toi10)
_NAT_SPLIT_RE = re.compile(r"(\d+)")


def natural_sort_key(s: str):
    """Breaks strings into numbers and text for natural sorting."""
    return [
        int(chunk) if chunk.isdigit() else chunk.lower()
        for chunk in _NAT_SPLIT_RE.split(s)
    ]


class ProblemListExtension(MDXExtension):
    """Registers the !problemlist tag as a preprocessor."""

    def __init__(self, problems_dir="docs/problems", **kwargs):
        self.problems_dir = Path(problems_dir)
        super().__init__(**kwargs)

    def extendMarkdown(self, md):
        md.registerExtension(self)
        md.preprocessors.register(
            ProblemListPreprocessor(self.problems_dir), "problemlist", 175
        )


class ProblemListPreprocessor(MDXPreprocessor):
    """Finds !problemlist in markdown and replaces with a generated grid."""

    tag = re.compile(r"!problemlist")

    def __init__(self, problems_dir):
        super().__init__()
        self.problems_dir = problems_dir

    def run(self, lines):
        new_lines = []
        for line in lines:
            if self.tag.search(line):
                new_lines.append(self.build_cards())  # Replace with generated HTML
            else:
                new_lines.append(line)
        return new_lines

    def build_cards(self):
        problems = []

        # Collect problems from problems_dir
        for file in os.listdir(self.problems_dir):
            if not file.endswith(".md"):
                continue
            pid, _ = os.path.splitext(file)
            if pid == "index":
                continue

            file_path = self.problems_dir / file
            title, source, difficulty, link = pid, "Unknown", "?", None

            # Parse YAML frontmatter if present
            if file_path.exists():
                try:
                    with open(file_path, encoding="utf-8") as f:
                        lines = f.readlines()
                except OSError:
                    lines = []

                if lines and lines[0].strip() == "---":
                    meta_lines = []
                    for line in lines[1:]:
                        if line.strip() == "---":
                            break
                        meta_lines.append(line)
                    try:
                        meta = yaml.safe_load("".join(meta_lines)) or {}
                    except yaml.YAMLError:
                        meta = {}

                    title = meta.get("title", pid) or pid
                    source = meta.get("source", "Unknown")
                    difficulty = meta.get("difficulty", "?")
                    link = meta.get("link")

            problems.append(
                {
                    "pid": pid,
                    "title": title,
                    "source": source,
                    "difficulty": difficulty,
                    "link": link,
                }
            )

        # Natural sort by pid (so toi2 < toi10)
        problems.sort(key=lambda x: natural_sort_key(x["pid"]))

        # Build the grid cards
        rows = []
        for p in problems:
            pid = p["pid"]
            title = p["title"]
            source = p["source"]
            difficulty = p["difficulty"]
            link = p["link"]

            card = (
                f'-   <a href="{link}" target="_blank" rel="noopener noreferrer">**{title}**</a>'
                if link
                else f"-   **{title}**"
            )
            rows.append(card)
            rows.append(f"    **Source**: {source}")
            rows.append(f"    **Difficulty**: {difficulty}")
            rows.append(
                f'    <a href="/problems/{pid}/" target="_blank" rel="noopener noreferrer">**View Solution** :material-open-in-new:</a>'
            )

        table = '<div class="grid cards" markdown>\n'
        table += "\n\n".join(rows)
        table += "\n\n</div>"
        return table


def makeExtension(**kwargs):
    return ProblemListExtension(**kwargs)
