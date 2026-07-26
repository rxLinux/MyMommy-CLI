import typer
from mymommy.ui.app import MyMommyApp
from mymommy.config.settings import settings

app = typer.Typer(name="MyMommy-CLI")

@app.command()
def start(
    watch: bool = typer.Option(False, "--watch", "-w", help="Enable watch mode"),
    model: str = typer.Option(None, "--model", "-m", help="Specify model to use")
):
    """Start MyMommy-CLI TUI."""
    if model:
        settings.DEFAULT_MODEL = model
    
    tui = MyMommyApp()
    tui.run()

@app.command()
def backend():
    """Start the licensing backend server."""
    import uvicorn
    uvicorn.run("mymommy.backend.main:app", host="0.0.0.0", port=8000, reload=True)

@app.command()
def install_bin():
    """Install the my-mommy executable globally into /usr/local/bin/."""
    import sys
    import os
    import subprocess
    from pathlib import Path
    
    # Locate the active my-mommy executable
    venv_bin = Path(sys.executable).parent / "my-mommy"
    if not venv_bin.exists():
        # Fallback to absolute workspace venv path
        venv_bin = Path("/home/otk_ruy/MyMommy-CLI/venv/bin/my-mommy")
        
    if not venv_bin.exists():
        typer.echo("❌ Erro: Não foi possível localizar o executável 'my-mommy' no ambiente virtual.")
        raise typer.Exit(code=1)
        
    target = Path("/usr/local/bin/my-mommy")
    
    typer.echo(f"Instalando link simbólico para {target}...")
    
    # Create symlink, using sudo if write permission is missing in /usr/local/bin
    if os.access("/usr/local/bin", os.W_OK):
        try:
            if target.is_symlink() or target.exists():
                target.unlink()
            target.symlink_to(venv_bin)
            typer.echo("✨ MyMommy-CLI instalado globalmente em /usr/local/bin/my-mommy!")
        except Exception as e:
            typer.echo(f"❌ Erro ao criar link: {str(e)}")
    else:
        typer.echo("ℹ️ Permissão de escrita ausente para /usr/local/bin. Solicitando sudo...")
        cmd = f"sudo ln -sf {venv_bin.resolve()} {target}"
        try:
            subprocess.run(cmd, shell=True, check=True)
            typer.echo("✨ MyMommy-CLI instalado globalmente em /usr/local/bin/my-mommy!")
        except subprocess.CalledProcessError:
            typer.echo("❌ Erro: Falha ao obter privilégios via sudo.")

if __name__ == "__main__":
    app()
