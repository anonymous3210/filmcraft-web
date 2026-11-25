#!/usr/bin/env python3
"""Serve the compiled FilmCraft Web app locally over HTTP."""

from __future__ import annotations

import argparse
import gzip
import re
import sys
import webbrowser
from functools import partial
from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path

BUILD_RE = re.compile(r'\bconst\s+build\s*=\s*["\']([0-9a-f]{16})["\']\s*;')
WASM_MAGIC = b"\x00asm\x01\x00\x00\x00"


def check_web_root(root: Path) -> tuple[bool, str]:
    index = root / "index.html"
    glue = root / "filmcraft_web.js"
    if not index.is_file() or not glue.is_file():
        return False, "faltam index.html ou filmcraft_web.js"

    try:
        html = index.read_text(encoding="utf-8")
    except OSError as exc:
        return False, f"não foi possível ler index.html: {exc}"

    match = BUILD_RE.search(html)
    if not match:
        return False, "não encontrei o hash do build em index.html"

    wasm_gz = root / f"filmcraft_web_bg_{match.group(1)}.wasm.gz"
    if not wasm_gz.is_file():
        return False, f"não encontrei {wasm_gz.name}"

    try:
        with gzip.open(wasm_gz, "rb") as wasm:
            if wasm.read(8) != WASM_MAGIC:
                return False, f"{wasm_gz.name} não contém um módulo WebAssembly válido"
    except (OSError, EOFError) as exc:
        return False, f"não foi possível validar {wasm_gz.name}: {exc}"

    return True, wasm_gz.name


def choose_web_root(script_dir: Path, requested: str | None) -> tuple[Path, str]:
    if requested:
        candidates = [Path(requested).expanduser().resolve()]
    else:
        candidates = [script_dir / "public", script_dir]

    reasons = []
    for candidate in candidates:
        ok, detail = check_web_root(candidate)
        if ok:
            return candidate.resolve(), detail
        reasons.append(f"{candidate}: {detail}")

    joined = "\n  ".join(reasons)
    raise SystemExit(
        "Não encontrei um build compilado do FilmCraft Web. Extraia o ZIP do app ou use --root.\n"
        f"  {joined}"
    )


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Executa o FilmCraft Web localmente e imprime a URL para abrir no navegador escolhido."
    )
    parser.add_argument("--root", help="pasta que contém index.html, o JavaScript e o WASM compactado")
    parser.add_argument("--host", default="127.0.0.1", help="interface de rede (padrão: somente neste computador)")
    parser.add_argument("--port", type=int, default=8000, help="porta HTTP (padrão: 8000)")
    parser.add_argument("--open", action="store_true", help="abrir a URL no navegador padrão do sistema")
    args = parser.parse_args()

    if sys.version_info < (3, 7):
        print("Erro: este script requer Python 3.7 ou mais recente.", file=sys.stderr)
        return 2
    if not 1 <= args.port <= 65535:
        print("Erro: --port deve estar entre 1 e 65535.", file=sys.stderr)
        return 2

    script_dir = Path(__file__).resolve().parent
    root, wasm_name = choose_web_root(script_dir, args.root)
    handler = partial(SimpleHTTPRequestHandler, directory=str(root))

    try:
        server = ThreadingHTTPServer((args.host, args.port), handler)
    except OSError as exc:
        print(f"Não consegui abrir {args.host}:{args.port}: {exc}", file=sys.stderr)
        print("Tente outra porta, por exemplo: python run_filmcraft_web.py --port 8080", file=sys.stderr)
        return 1

    display_host = "127.0.0.1" if args.host in ("0.0.0.0", "::") else args.host
    url = f"http://{display_host}:{server.server_port}/"
    print(f"FilmCraft Web está servindo em: {url}", flush=True)
    print(f"Pasta: {root}", flush=True)
    print(f"WASM: {wasm_name}", flush=True)
    print("Abra essa URL no navegador que preferir. Mantenha esta janela aberta; Ctrl+C encerra o servidor.", flush=True)

    if args.open:
        webbrowser.open(url, new=2)

    try:
        server.serve_forever()
    except KeyboardInterrupt:
        print("\nServidor encerrado.", flush=True)
    finally:
        server.server_close()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
