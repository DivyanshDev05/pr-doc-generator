"""
doc_writer.py — Writes the generated PR document to disk.
Filename is derived from the branch name exactly.
"""

import os
import re
from datetime import datetime


def _branch_to_filename(branch_name: str) -> str:
    """
    Convert a branch name to a safe filename.
    e.g. 'feature/PROJ-703-fix-sonar' → 'feature_PROJ-703-fix-sonar'
    e.g. 'bugfix/PROJ-29-client-reg'   → 'bugfix_PROJ-29-client-reg'
    """
    # Replace path separators with underscores, keep hyphens and alphanumerics
    safe = re.sub(r"[/\\]", "_", branch_name)
    safe = re.sub(r"[^\w\-]", "_", safe)
    safe = re.sub(r"_+", "_", safe).strip("_")
    return safe


class DocWriter:
    def __init__(self, output_dir: str):
        self.output_dir = output_dir
        os.makedirs(output_dir, exist_ok=True)

    def write(self, content: str, branch_name: str) -> str:
        """
        Write the PR doc to output_dir/<branch_name>.md
        If file already exists, append a timestamp to avoid overwriting.
        """
        filename = _branch_to_filename(branch_name) + ".md"
        output_path = os.path.join(self.output_dir, filename)

        # Avoid overwriting — append timestamp if file exists
        if os.path.exists(output_path):
            ts = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = _branch_to_filename(branch_name) + f"_{ts}.md"
            output_path = os.path.join(self.output_dir, filename)

        with open(output_path, "w", encoding="utf-8") as f:
            f.write(content)

        return output_path
