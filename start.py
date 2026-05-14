#!/usr/bin/env python3
"""
Van Já — Launcher
Sobe backend (FastAPI) + frontend (HTTP server) + abre o navegador.
Ctrl+C encerra tudo.
"""
import os
import subprocess
import sys
import time
import webbrowser
from pathlib import Path

ROOT = Path(__file__).parent.resolve()
BACKEND = ROOT / "backend"
FRONTEND = ROOT / "frontend"
VENV_PYTHON = ROOT / "venv" / "bin" / "python"

BACKEND_PORT = 8000
FRONTEND_PORT = 5500
FRONTEND_URL = f"http://localhost:{FRONTEND_PORT}/index.html"


def python_bin() -> str:
    """Usa o python do venv se existir; senão o python do sistema."""
    if VENV_PYTHON.exists():
        return str(VENV_PYTHON)
    return sys.executable


def main() -> None:
    py = python_bin()
    print("=" * 60)
    print("  Van Já — iniciando serviços…")
    print("=" * 60)
    print(f"  Python:   {py}")
    print(f"  Backend:  http://localhost:{BACKEND_PORT}")
    print(f"  Frontend: {FRONTEND_URL}")
    print("=" * 60)
    print()

    if not (BACKEND / "main.py").exists():
        print(f"ERRO: backend não encontrado em {BACKEND}")
        sys.exit(1)
    if not (FRONTEND / "index.html").exists():
        print(f"ERRO: frontend não encontrado em {FRONTEND}")
        sys.exit(1)

    backend_proc = subprocess.Popen(
        [py, "-m", "uvicorn", "main:app", "--host", "127.0.0.1", "--port", str(BACKEND_PORT)],
        cwd=str(BACKEND),
    )

    frontend_proc = subprocess.Popen(
        [py, "-m", "http.server", str(FRONTEND_PORT), "--directory", str(FRONTEND)],
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
    )

    # Espera um instante e abre o navegador
    time.sleep(1.5)
    try:
        webbrowser.open(FRONTEND_URL)
    except Exception:
        pass

    print()
    print("→ Acesse:", FRONTEND_URL)
    print("→ Pressione Ctrl+C para encerrar.")
    print()

    try:
        backend_proc.wait()
    except KeyboardInterrupt:
        print("\nEncerrando…")
    finally:
        for p in (backend_proc, frontend_proc):
            try:
                p.terminate()
                p.wait(timeout=5)
            except Exception:
                try:
                    p.kill()
                except Exception:
                    pass
        print("Pronto.")


if __name__ == "__main__":
    main()
