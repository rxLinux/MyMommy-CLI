import os
from pathlib import Path
from mymommy.sandbox.sandbox import Sandbox

class ProjectIndexer:
    def __init__(self, sandbox: Sandbox):
        self.sandbox = sandbox

    def get_project_summary(self) -> str:
        """
        Generates a summary of the project:
        - Files list
        - README content (if any)
        - Key files (package.json, pyproject.toml, etc.)
        """
        summary = ["PROJECT SUMMARY:"]
        
        # 1. Structure
        files = self.sandbox.list_files(".")
        summary.append("\nRoot files:")
        for f in files:
            summary.append(f"- {f.name}")

        # 2. README
        readme = self._find_readme()
        if readme:
            content = self.sandbox.read_file(readme)
            summary.append(f"\nREADME Content (first 500 chars):\n{content[:500]}...")

        # 3. Dependencies
        deps = self._find_dependencies()
        if deps:
            summary.append(f"\nFound dependency files: {', '.join(deps)}")

        return "\n".join(summary)

    def _find_readme(self) -> str | None:
        for f in ["README.md", "README", "readme.md"]:
            if (self.sandbox.base_path / f).exists():
                return f
        return None

    def _find_dependencies(self) -> list[str]:
        found = []
        for f in ["package.json", "pyproject.toml", "requirements.txt", "Gemfile", "go.mod"]:
            if (self.sandbox.base_path / f).exists():
                found.append(f)
        return found
