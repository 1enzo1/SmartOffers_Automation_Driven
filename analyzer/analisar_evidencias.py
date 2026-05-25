import json
import os
from pathlib import Path

from core.utils.evidence_analysis import analisar_teste


def executar():
    choice = input("Escolha a base path:\n1 - '1. Evidências'\n2 - '2. Evidências variante'\n> ")
    base_path = "evidencias" if choice == "1" else "evidencias_variante"

    base = Path(base_path)
    if not base.exists():
        return

    pastas = sorted(
        {
            arquivo.parent
            for arquivo in base.rglob("*.json")
            if arquivo.parent != base
        },
        key=str,
    )

    for pasta in pastas:
        rel = pasta.relative_to(base)
        partes = rel.parts
        tipo = partes[-2] if len(partes) >= 2 else partes[0]

        resultado = analisar_teste(str(pasta), tipo)

        print("\n========================")
        print(" - ".join(partes))
        print(json.dumps(resultado, indent=2, ensure_ascii=False))


if __name__ == "__main__":
    executar()
