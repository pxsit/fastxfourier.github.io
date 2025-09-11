import re
import yaml
import os
from pathlib import Path
from markdown.extensions import Extension
from markdown.preprocessors import Preprocessor

class ProblemCardsExtension(Extension):
    def __init__(self, problems_dir="docs/problems", **kwargs):
        self.problems_dir = Path(problems_dir)
        super().__init__(**kwargs)

    def extendMarkdown(self, md):
        md.registerExtension(self)
        md.preprocessors.register(
            ProblemCardsPreprocessor(self.problems_dir), 'problem_cards', 175
        )

class ProblemCardsPreprocessor(Preprocessor):
    tag = re.compile(r"!problem_all")

    def __init__(self, problems_dir):
        super().__init__()
        self.problems_dir = Path(problems_dir)

    def run(self, lines):
        new_lines = []
        for line in lines:
            if self.tag.search(line):
                html = self.build_cards()
                new_lines.append(html)
            else:
                new_lines.append(line)
        return new_lines

    def build_cards(self):
        cards = []
        for f in sorted(os.listdir(self.problems_dir)):
            if not f.endswith(".md") or f == "index.md":
                continue

            file_path = self.problems_dir / f
            meta = {}
            with open(file_path, encoding="utf-8") as fh:
                lines = fh.readlines()
                if lines and lines[0].strip() == "---":
                    meta_lines = []
                    for line in lines[1:]:
                        if line.strip() == "---":
                            break
                        meta_lines.append(line)
                    meta = yaml.safe_load("".join(meta_lines)) or {}

            title = meta.get("title", f)
            source = meta.get("source", "?")
            tags = meta.get("tags", "")
            solution = meta.get("solution", f"/problems/{f.replace('.md','')}")

            card_html = f"""
<div class="problem-card">
  <div class="header">
    <span class="title">{title}</span>
    <span class="source">{source}</span>
  </div>
  <details class="tags-spoiler">
    <summary>Tags</summary>
    <div class="tags">{tags}</div>
  </details>
  <div class="view-solution"><a href="{solution}" target="_blank">View Solution</a></div>
</div>
"""
            cards.append(card_html)

        return '<div class="problem-grid">\n' + "\n".join(cards) + '\n</div>'

def makeExtension(**kwargs):
    return ProblemCardsExtension(**kwargs)
