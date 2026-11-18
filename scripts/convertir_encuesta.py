"""
Convierte las respuestas de Google Forms (CSV descargado) al archivo que usa el modelo
y revisa la consistencia de cada persona.

Uso:
  python scripts/convertir_encuesta.py ruta/al/archivo_de_forms.csv
  python scripts/convertir_encuesta.py ruta/al/archivo_de_forms.csv --excluir-inconsistentes

Las 15 preguntas deben estar en el mismo orden que PARES. Cada opcion de respuesta
termina con su valor entre parentesis, por ejemplo "(5)" o "(1/5)".
"""
import argparse
import csv
import math
import re
import sys
from fractions import Fraction
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
CRITERIOS = ["throughput", "latencia_p95", "ram", "cpu", "loc", "popularidad"]
PARES = [(a, b) for i, a in enumerate(CRITERIOS) for b in CRITERIOS[i + 1:]]
PATRON = re.compile(r"\((\d+(?:/\d+)?)\)\s*$")


def razon_consistencia(matriz):
    n = len(matriz)
    sumas = [sum(matriz[i][j] for i in range(n)) for j in range(n)]
    pesos = [sum(matriz[i][j] / sumas[j] for j in range(n)) / n for i in range(n)]
    n_max = sum(sum(matriz[i][j] * pesos[j] for j in range(n)) for i in range(n))
    ic = (n_max - n) / (n - 1)
    ia = 1.98 * (n - 2) / n
    return ic / ia


def main():
    p = argparse.ArgumentParser()
    p.add_argument("csv_forms")
    p.add_argument("--excluir-inconsistentes", action="store_true",
                   help="no incluir a quienes tengan RC >= 0.10")
    args = p.parse_args()

    with open(args.csv_forms, encoding="utf-8-sig") as fh:
        filas = list(csv.reader(fh))
    encabezado, respuestas = filas[0], filas[1:]

    # Columnas de preguntas AHP: las que tienen valores con "(x)" al final
    columnas = [j for j in range(len(encabezado))
                if any(PATRON.search(r[j]) for r in respuestas if j < len(r))]
    if len(columnas) != len(PARES):
        sys.exit(f"Se esperaban {len(PARES)} preguntas de comparacion y se encontraron {len(columnas)}.")

    salida = []
    print(f"{'Persona':<8} {'RC':>8}  Estado")
    for k, r in enumerate(respuestas, 1):
        persona = f"P{k}"
        valores = []
        for j in columnas:
            m = PATRON.search(r[j]) if j < len(r) else None
            if not m:
                valores = None
                break
            valores.append(float(Fraction(m.group(1))))
        if valores is None:
            print(f"{persona:<8} {'-':>8}  incompleta, se omite")
            continue
        n = len(CRITERIOS)
        matriz = [[1.0] * n for _ in range(n)]
        for (a, b), v in zip(PARES, valores):
            i, j = CRITERIOS.index(a), CRITERIOS.index(b)
            matriz[i][j], matriz[j][i] = v, 1 / v
        rc = razon_consistencia(matriz)
        consistente = rc < 0.10
        estado = "consistente" if consistente else "INCONSISTENTE"
        if not consistente and args.excluir_inconsistentes:
            estado += " -> excluida"
        print(f"{persona:<8} {rc:>8.4f}  {estado}")
        if consistente or not args.excluir_inconsistentes:
            for (a, b), m in zip(PARES, [PATRON.search(r[j]).group(1) for j in columnas]):
                salida.append([persona, a, b, m])

    destino = ROOT / "modelo" / "datos" / "ahp_respuestas.csv"
    with destino.open("w", newline="", encoding="utf-8") as fh:
        w = csv.writer(fh)
        w.writerow(["persona", "criterio_a", "criterio_b", "valor"])
        w.writerows(salida)
    personas = len({f[0] for f in salida})
    print(f"\n{personas} personas guardadas en {destino.relative_to(ROOT)}")
    print("Ahora ejecuten: python modelo/modelo_decision.py")


if __name__ == "__main__":
    main()
