"""CLI wrapper for java_helper (optional)."""
import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from app.services.java_helper import find_java_exes, locate_vortex_conf, update_java_path

def main():
    if len(sys.argv) < 2:
        print("Uso: python tools/java_path_helper.py <pasta_do_java> [caminho_java_exe]")
        sys.exit(1)
    folder = Path(sys.argv[1])
    exes = find_java_exes(folder)
    if not exes:
        print("Nenhum java.exe encontrado.")
        sys.exit(1)
    if len(sys.argv) >= 3:
        chosen = Path(sys.argv[2])
    elif len(exes) == 1:
        chosen = exes[0]
    else:
        print("Múltiplos encontrados:")
        for i, p in enumerate(exes):
            print(f"  {i}: {p}")
        idx = int(input("Escolha índice: ").strip())
        chosen = exes[idx]
    conf = locate_vortex_conf()
    if not conf:
        print("vortex_launcher.conf não encontrado.")
        sys.exit(1)
    ok, msg = update_java_path(conf, chosen)
    print(msg)
    sys.exit(0 if ok else 1)

if __name__ == "__main__":
    main()
