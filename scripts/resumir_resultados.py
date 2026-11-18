"""
Lee los datos crudos de las pruebas (k6 + docker stats), calcula promedio y
desviacion estandar de cada metrica y arma la tabla de entrada del modelo.

Salidas:
  resultados/mediciones.csv        una fila por repeticion (datos crudos resumidos)
  resultados/resumen.csv           promedio y desviacion por lenguaje
  modelo/datos/datos_modelo.csv    tabla que usa el modelo de decision
"""
import csv
import json
import re
import statistics
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
RAW = ROOT / "resultados" / "raw"
ALTERNATIVAS = {
    "python": ("Python (FastAPI)", ROOT / "apis/python-fastapi/main.py"),
    "node": ("Node.js (Express)", ROOT / "apis/node-express/server.js"),
    "csharp": ("C# (.NET)", ROOT / "apis/csharp-dotnet/Program.cs"),
}
METRICAS = ["throughput_rps", "latencia_p95_ms", "latencia_prom_ms", "tasa_error_pct", "ram_mb", "cpu_pct"]

UNIDADES = {"b": 1 / 1e6, "kib": 1024 / 1e6, "kb": 1e3 / 1e6, "mib": 1024**2 / 1e6,
            "mb": 1.0, "gib": 1024**3 / 1e6, "gb": 1e3}


def a_mb(texto):
    """Convierte '123.4MiB' a megabytes."""
    m = re.match(r"\s*([\d.]+)\s*([a-zA-Z]+)", texto)
    valor, unidad = float(m.group(1)), m.group(2).lower()
    return valor * UNIDADES[unidad]


def leer_stats(ruta):
    cpu, ram = [], []
    for linea in ruta.read_text(encoding="utf-8").splitlines():
        partes = linea.strip().split(",")
        if len(partes) != 2 or "%" not in partes[0]:
            continue
        cpu.append(float(partes[0].replace("%", "")))
        ram.append(a_mb(partes[1].split("/")[0]))
    if not cpu:
        raise ValueError(f"Sin muestras de docker stats en {ruta.name}")
    # La primera y la ultima muestra caen antes o despues de la carga: se descartan
    if len(cpu) >= 5:
        cpu, ram = cpu[1:-1], ram[1:-1]
    return statistics.mean(cpu), statistics.mean(ram)


def leer_k6(ruta):
    m = json.loads(ruta.read_text(encoding="utf-8"))["metrics"]
    return {
        "throughput_rps": m["http_reqs"]["rate"],
        "latencia_p95_ms": m["http_req_duration"]["p(95)"],
        "latencia_prom_ms": m["http_req_duration"]["avg"],
        "tasa_error_pct": m["http_req_failed"]["value"] * 100,
    }


def contar_loc(ruta):
    """Lineas de codigo: sin lineas vacias ni lineas que solo son comentarios."""
    total = 0
    for linea in ruta.read_text(encoding="utf-8").splitlines():
        s = linea.strip()
        if s and not s.startswith(("#", "//")):
            total += 1
    return total


def leer_popularidad():
    """Porcentaje de uso del framework (Stack Overflow Developer Survey 2025)."""
    ruta = ROOT / "modelo" / "datos" / "popularidad.csv"
    with ruta.open(encoding="utf-8") as f:
        return {fila["alternativa"]: float(fila["uso_pct"]) for fila in csv.DictReader(f)}


def main():
    mediciones = []
    for alias, (nombre, _) in ALTERNATIVAS.items():
        for ruta in sorted(RAW.glob(f"{alias}_rep*.json"), key=lambda p: int(re.search(r"rep(\d+)", p.name).group(1))):
            rep = int(re.search(r"rep(\d+)", ruta.name).group(1))
            fila = {"alternativa": nombre, "repeticion": rep, **leer_k6(ruta)}
            fila["cpu_pct"], fila["ram_mb"] = leer_stats(RAW / f"{alias}_rep{rep}_stats.csv")
            mediciones.append(fila)

    if not mediciones:
        raise SystemExit("No hay resultados en resultados/raw. Ejecuta primero scripts/ejecutar_pruebas.sh")

    salida = ROOT / "resultados"
    with (salida / "mediciones.csv").open("w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=["alternativa", "repeticion", *METRICAS])
        w.writeheader()
        for fila in mediciones:
            w.writerow({k: (round(v, 4) if isinstance(v, float) else v) for k, v in fila.items()})

    resumen = {}
    with (salida / "resumen.csv").open("w", newline="", encoding="utf-8") as f:
        w = csv.writer(f)
        w.writerow(["alternativa", "metrica", "n", "promedio", "desviacion"])
        for alias, (nombre, _) in ALTERNATIVAS.items():
            filas = [m for m in mediciones if m["alternativa"] == nombre]
            resumen[nombre] = {}
            for met in METRICAS:
                valores = [m[met] for m in filas]
                prom = statistics.mean(valores)
                desv = statistics.stdev(valores) if len(valores) > 1 else 0.0
                resumen[nombre][met] = prom
                w.writerow([nombre, met, len(valores), round(prom, 4), round(desv, 4)])

    popularidad = leer_popularidad()

    destino = ROOT / "modelo" / "datos" / "datos_modelo.csv"
    with destino.open("w", newline="", encoding="utf-8") as f:
        w = csv.writer(f)
        w.writerow(["alternativa", "throughput", "latencia_p95", "ram", "cpu", "loc", "popularidad", "tasa_error"])
        for alias, (nombre, fuente) in ALTERNATIVAS.items():
            r = resumen[nombre]
            w.writerow([nombre, round(r["throughput_rps"], 2), round(r["latencia_p95_ms"], 2),
                        round(r["ram_mb"], 2), round(r["cpu_pct"], 2), contar_loc(fuente),
                        popularidad[nombre], round(r["tasa_error_pct"], 3)])

    print(f"Mediciones: {len(mediciones)} filas -> resultados/mediciones.csv")
    print("Promedios y desviaciones -> resultados/resumen.csv")
    print(f"Tabla del modelo -> {destino.relative_to(ROOT)}")


if __name__ == "__main__":
    main()
