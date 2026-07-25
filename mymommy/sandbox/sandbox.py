import os
from pathlib import Path
from typing import Union

class SandboxError(Exception):
    """Exception raised for sandbox violations."""
    pass

class Sandbox:
    """
    Ensures all file operations stay within the current working directory.
    """
    def __init__(self, base_path: Union[str, Path] = None):
        if base_path is None:
            self.base_path = Path.cwd().resolve()
        else:
            self.base_path = Path(base_path).resolve()

    def validate_path(self, path: Union[str, Path]) -> Path:
        """
        Validates that a path is within the base_path.
        Returns the absolute Path if valid, otherwise raises SandboxError.
        """
        p = Path(path)
        
        # Check if the path is a real physical absolute path within our base_path
        try:
            p_resolved = p.resolve()
            p_resolved.relative_to(self.base_path)
            return p_resolved
        except (ValueError, RuntimeError):
            pass

        # If the path is absolute but not physically inside our base_path
        if p.is_absolute():
            # Known system directories that should never be mapped relatively
            system_roots = {"home", "tmp", "etc", "usr", "bin", "lib", "var", "sys", "proc", "dev", "opt", "sbin", "boot"}
            
            # Extract the first directory part
            first_dir = p.parts[1] if len(p.parts) > 1 else ""
            
            if first_dir in system_roots:
                # System absolute path: resolve as absolute, which will fail validation
                target_path = p.resolve()
            else:
                # Project-shorthand absolute path (like /src/main.py): strip root and treat as relative to base_path
                relative_parts = p.parts[1:] if (p.drive or p.root) else p.parts
                target_path = (self.base_path / Path(*relative_parts)).resolve()
        else:
            target_path = (self.base_path / p).resolve()
        
        # Double check that the final target path is strictly within the base path
        try:
            target_path.relative_to(self.base_path)
        except ValueError:
            raise SandboxError(f"Access denied: Path '{path}' is outside the allowed directory '{self.base_path}'.")
        
        return target_path

    def is_safe(self, path: Union[str, Path]) -> bool:
        """Checks if a path is safe without raising an exception."""
        try:
            self.validate_path(path)
            return True
        except SandboxError:
            return False

    def list_files(self, relative_path: str = ".") -> list[Path]:
        """Lists files in a safe way."""
        safe_dir = self.validate_path(relative_path)
        return [p for p in safe_dir.iterdir()]

    def read_file(self, path: str) -> str:
        """Reads a file safely."""
        safe_path = self.validate_path(path)
        if not safe_path.is_file():
            raise SandboxError(f"'{path}' is not a file.")
        return safe_path.read_text(encoding="utf-8")

    def write_file(self, path: str, content: str) -> None:
        """Writes a file safely, creating parent folders automatically."""
        safe_path = self.validate_path(path)
        safe_path.parent.mkdir(parents=True, exist_ok=True)
        safe_path.write_text(content, encoding="utf-8")
