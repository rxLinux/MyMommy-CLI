# MyMommy-CLI Project Instructions

## Architecture
- **Sandbox**: Mandatory `Sandbox` class to restrict file access to `cwd`.
- **Tools**: Independent modules in `mymommy/tools/` (FileTool, ShellTool, etc.).
- **Models**: Flexible provider system in `mymommy/models/`, defaulting to Ollama.
- **Memory**: Project-specific data in `.mymommy/` using SQLite for history.
- **UI**: Textual-based TUI with a modern, "Codex CLI" inspired look.
- **Licensing**: FREE (450k tokens) vs PRO. Backend handles payments (Mercado Pago).

## Standards
- Python 3.12+ features (type hints, f-strings).
- SOLID principles.
- Use Pydantic for data structures.
- Use Rich for terminal formatting.
- Comprehensive testing with pytest.

## Core Rules
- **SECURITY**: Never access files outside `cwd`.
- **UX**: Professional, aesthetic, and responsive TUI.
- **Agent**: Plan -> Execute -> Validate -> Correct loop.
