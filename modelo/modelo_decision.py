"""
Modelo de decision multicriterio ponderado para elegir el lenguaje de backend.

Pasos (los mismos que se resuelven a mano):
  1. Pesos con el proceso de jerarquia analitica (PJA / AHP) y razon de consistencia
  2. Filtro de restricciones duras
  3. Normalizacion  (max: x / max   |   min: min / x)
  4. Puntaje global S_i = sum(w_j * r_ij) y ranking
  + Casos de prueba, analisis de sensibilidad (peso critico) y grafica

Uso:
  python modelo/modelo_decision.py                      # usa modelo/datos/datos_modelo.csv
  python modelo/modelo_decision.py --datos modelo/datos/datos_modelo_EJEMPLO.csv
  python modelo/modelo_decision.py --ri saaty           # indice aleatorio de Saaty en lugar del de Taha
"""
import argparse
import csv
import json
import math
from fractions import Fraction
from pathlib import Path

DIR = Path(__file__).resolve().parent
DATOS = DIR / "datos"
DEC = 4  # decimales que se muestran (usen los mismos en la solucion manual)

LINEAS = []


def out(texto=""):
    print(texto)
    LINEAS.append(texto)


def f(x):
    return f"{x:.{DEC}f}"


# --------------------------------------------------------------------------- lectura

def leer_csv(ruta):
    with open(ruta, encoding="utf-8") as fh:
        return list(csv.DictReader(fh))


def a_numero(texto):
    return float(Fraction(texto.strip()))


def leer_criterios():
    return leer_csv(DATOS / "criterios.csv")


def leer_alternativas(ruta, claves):
    filas = leer_csv(ruta)
    return [{"nombre": fila["alternativa"],
             **{k: float(fila[k]) for k in fila if k != "alternativa"}} for fila in filas]


def leer_restricciones():
    return [{"clave": r["clave"], "operador": r["operador"], "umbral": float(r["umbral"]),
             "justificacion": r.get("justificacion", "")}
            for r in leer_csv(DATOS / "restricciones.csv")]


def matriz_desde_respuestas(ruta, claves):
    """Une las respuestas de la encuesta con la media geometrica (una matriz por persona)."""
    filas = [r for r in leer_csv(ruta) if r["valor"].strip()]
    personas = sorted({r["persona"] for r in filas})
    n = len(claves)
    matrices = []
    for p in personas:
        m = [[1.0] * n for _ in range(n)]
        for r in (x for x in filas if x["persona"] == p):
            i, j = claves.index(r["criterio_a"]), claves.index(r["criterio_b"])
            v = a_numero(r["valor"])
            m[i][j], m[j][i] = v, 1 / v
        matrices.append(m)
    media = [[math.prod(m[i][j] for m in matrices) ** (1 / len(matrices)) for j in range(n)]
             for i in range(n)]
    return media, personas


def leer_matriz_ahp(claves):
    respuestas = DATOS / "ahp_respuestas.csv"
    if respuestas.exists() and any(r["valor"].strip() for r in leer_csv(respuestas)):
        matriz, personas = matriz_desde_respuestas(respuestas, claves)
        out(f"Matriz obtenida de la encuesta ({len(personas)} personas) con media geometrica.")
        return matriz
    filas = {r["criterio"]: r for r in leer_csv(DATOS / "ahp_matriz.csv")}
    out("Matriz tomada de modelo/datos/ahp_matriz.csv")
    return [[a_numero(filas[i][j]) for j in claves] for i in claves]


# --------------------------------------------------------------------------- AHP

def indice_aleatorio(n, metodo):
    if metodo == "saaty":
        tabla = {1: 0, 2: 0, 3: 0.58, 4: 0.90, 5: 1.12, 6: 1.24, 7: 1.32, 8: 1.41, 9: 1.45, 10: 1.49}
        return tabla[n], f"tabla de Saaty para n = {n}"
    return 1.98 * (n - 2) / n, f"1.98(n - 2)/n = 1.98({n} - 2)/{n}"


def ahp(matriz, claves, nombres, metodo_ri):
    n = len(claves)
    out("\nMatriz de comparacion por pares A:")
    tabla(["", *claves], [[claves[i], *[f(v) for v in matriz[i]]] for i in range(n)])

    sumas = [sum(matriz[i][j] for i in range(n)) for j in range(n)]
    out("\nSuma de cada columna:")
    for j in range(n):
        out(f"  {claves[j]}: " + " + ".join(f(matriz[i][j]) for i in range(n)) + f" = {f(sumas[j])}")

    norm = [[matriz[i][j] / sumas[j] for j in range(n)] for i in range(n)]
    out("\nMatriz normalizada (cada valor / suma de su columna):")
    tabla(["", *claves], [[claves[i], *[f(v) for v in norm[i]]] for i in range(n)])

    pesos = [sum(norm[i]) / n for i in range(n)]
    out("\nPesos w = promedio de cada fila:")
    for i in range(n):
        out(f"  w({claves[i]}) = ({' + '.join(f(v) for v in norm[i])}) / {n} = {f(pesos[i])}")
    out(f"  Comprobacion: suma de pesos = {f(sum(pesos))}")

    aw = [sum(matriz[i][j] * pesos[j] for j in range(n)) for i in range(n)]
    out("\nConsistencia:")
    out("  A x w:")
    for i in range(n):
        out(f"    fila {claves[i]}: " + " + ".join(f"{f(matriz[i][j])}*{f(pesos[j])}" for j in range(n))
            + f" = {f(aw[i])}")
    lam = sum(aw)
    ci = (lam - n) / (n - 1)
    ri, txt_ri = indice_aleatorio(n, metodo_ri)
    cr = ci / ri if ri else 0.0
    out(f"  n_max = suma de A x w = {' + '.join(f(v) for v in aw)} = {f(lam)}")
    out(f"  IC = (n_max - n) / (n - 1) = ({f(lam)} - {n}) / {n - 1} = {f(ci)}")
    out(f"  IA = {txt_ri} = {f(ri)}")
    out(f"  RC = IC / IA = {f(ci)} / {f(ri)} = {f(cr)}  ->  "
        + ("CONSISTENTE (RC < 0.10)" if cr < 0.10 else "INCONSISTENTE (RC >= 0.10): revisar los juicios"))
    return dict(zip(claves, pesos)), cr


# --------------------------------------------------------------------------- modelo

def cumple(valor, operador, umbral):
    return {"<=": valor <= umbral, ">=": valor >= umbral, "<": valor < umbral, ">": valor > umbral}[operador]


def evaluar(alternativas, criterios, pesos, restricciones, detalle=True):
    if detalle:
        out("\nPASO 2. Filtro de restricciones duras")
    factibles = []
    for a in alternativas:
        ok = True
        for r in restricciones:
            c = cumple(a[r["clave"]], r["operador"], r["umbral"])
            ok = ok and c
            if detalle:
                out(f"  {a['nombre']}: {r['clave']} = {a[r['clave']]:g} {r['operador']} {r['umbral']:g}  "
                    + ("cumple" if c else "NO CUMPLE -> se descarta"))
        if ok:
            factibles.append(a)
    if not factibles:
        if detalle:
            out("  Ninguna alternativa cumple las restricciones.")
        return []

    if detalle:
        out("\nPASO 3. Normalizacion")
    r = {a["nombre"]: {} for a in factibles}
    for c in criterios:
        k = c["clave"]
        valores = [a[k] for a in factibles]
        ref = max(valores) if c["tipo"] == "max" else min(valores)
        if detalle:
            regla = "x / max" if c["tipo"] == "max" else "min / x"
            out(f"  {c['nombre']} ({'maximizar' if c['tipo'] == 'max' else 'minimizar'}, {regla}, "
                f"{'max' if c['tipo'] == 'max' else 'min'} = {ref:g}):")
        for a in factibles:
            valor = a[k] / ref if c["tipo"] == "max" else ref / a[k]
            r[a["nombre"]][k] = valor
            if detalle:
                op = f"{a[k]:g} / {ref:g}" if c["tipo"] == "max" else f"{ref:g} / {a[k]:g}"
                out(f"    {a['nombre']}: {op} = {f(valor)}")

    if detalle:
        out("\nPASO 4. Puntaje global S = suma(w * r)")
    puntajes = []
    for a in factibles:
        partes = [pesos[c["clave"]] * r[a["nombre"]][c["clave"]] for c in criterios]
        s = sum(partes)
        puntajes.append((a["nombre"], s, r[a["nombre"]]))
        if detalle:
            terminos = " + ".join(f"{f(pesos[c['clave']])}*{f(r[a['nombre']][c['clave']])}" for c in criterios)
            out(f"  S({a['nombre']}) = {terminos}")
            out(f"      = {' + '.join(f(p) for p in partes)} = {f(s)}")
    puntajes.sort(key=lambda t: t[1], reverse=True)
    if detalle:
        out("\n  Ranking:")
        for pos, (nombre, s, _) in enumerate(puntajes, 1):
            out(f"    {pos}. {nombre}: {f(s)}")
    return puntajes


# --------------------------------------------------------------------------- sensibilidad

def sensibilidad(puntajes_base, criterios, pesos):
    """Para cada criterio k, S_i(t) = t*r_ik + (1 - t)/(1 - w_k) * sum_{j != k} w_j r_ij."""
    resultados = {}
    for c in criterios:
        k = c["clave"]
        wk = pesos[k]
        rectas = {}
        for nombre, _, r in puntajes_base:
            a = r[k]
            b = sum(pesos[j["clave"]] * r[j["clave"]] for j in criterios if j["clave"] != k) / (1 - wk)
            rectas[nombre] = (a, b)  # S(t) = b + (a - b) t

        def ganador(t):
            return max(rectas, key=lambda n: rectas[n][1] + (rectas[n][0] - rectas[n][1]) * t)

        cortes = set()
        nombres = list(rectas)
        for x in range(len(nombres)):
            for y in range(x + 1, len(nombres)):
                (a1, b1), (a2, b2) = rectas[nombres[x]], rectas[nombres[y]]
                den = (a1 - b1) - (a2 - b2)
                if abs(den) > 1e-12:
                    t = (b2 - b1) / den
                    if 0 < t < 1:
                        cortes.add(t)
        cambios = []
        prev = ganador(0)
        for t in sorted(cortes):
            nuevo = ganador(min(t + 1e-9, 1))
            if nuevo != prev:
                cambios.append((t, prev, nuevo))
                prev = nuevo
        resultados[k] = {"rectas": rectas, "cambios": cambios, "peso_base": wk}
    return resultados


def grafica(sens, criterios, ruta):
    try:
        import matplotlib
        matplotlib.use("Agg")
        import matplotlib.pyplot as plt
    except ImportError:
        out("(matplotlib no esta instalado: se omite la grafica)")
        return
    colores = ["#1f77b4", "#d62728", "#2ca02c", "#9467bd", "#ff7f0e"]
    n = len(criterios)
    filas = math.ceil(n / 3)
    fig, ejes = plt.subplots(filas, 3, figsize=(14, 4.2 * filas), squeeze=False)
    for idx, c in enumerate(criterios):
        ax = ejes[idx // 3][idx % 3]
        datos = sens[c["clave"]]
        for i, (nombre, (a, b)) in enumerate(datos["rectas"].items()):
            ax.plot([0, 1], [b, a], label=nombre, color=colores[i % len(colores)], linewidth=2)
        ax.axvline(datos["peso_base"], color="gray", linestyle="--", linewidth=1)
        ax.text(datos["peso_base"], ax.get_ylim()[1], f" base {datos['peso_base']:.3f}",
                va="top", fontsize=8, color="gray")
        for i, (t, _, _) in enumerate(datos["cambios"]):
            ax.axvline(t, color="black", linestyle=":", linewidth=1)
            ax.text(t, 0.02 + 0.08 * (i % 2), f" {t:.3f}", va="bottom", fontsize=8,
                    transform=ax.get_xaxis_transform())
        ax.set_title(f"Peso de {c['nombre']}")
        ax.set_xlabel("peso del criterio")
        ax.set_ylabel("puntaje S")
        ax.set_xlim(0, 1)
        ax.grid(alpha=0.3)
    for idx in range(n, filas * 3):
        ejes[idx // 3][idx % 3].axis("off")
    ejes[0][0].legend(fontsize=8)
    fig.suptitle("Analisis de sensibilidad: puntaje de cada lenguaje segun el peso de un criterio\n"
                 "(linea punteada negra = peso critico donde cambia el ganador)", fontsize=11)
    fig.tight_layout()
    fig.savefig(ruta, dpi=150)
    out(f"\nGrafica de sensibilidad guardada en {ruta}")


# --------------------------------------------------------------------------- utilidades

def tabla(encabezado, filas):
    anchos = [max(len(str(x)) for x in col) for col in zip(encabezado, *filas)]
    out("  " + " | ".join(str(h).ljust(w) for h, w in zip(encabezado, anchos)))
    out("  " + "-+-".join("-" * w for w in anchos))
    for fila in filas:
        out("  " + " | ".join(str(x).ljust(w) for x, w in zip(fila, anchos)))


def titulo(texto):
    out("\n" + "=" * 78)
    out(texto)
    out("=" * 78)


# --------------------------------------------------------------------------- principal

def main():
    p = argparse.ArgumentParser()
    p.add_argument("--datos", default=str(DATOS / "datos_modelo.csv"))
    p.add_argument("--ri", choices=["taha", "saaty"], default="taha")
    p.add_argument("--salida", default=str(DIR / "salidas"))
    args = p.parse_args()

    ruta_datos = Path(args.datos)
    if not ruta_datos.exists():
        raise SystemExit(f"No existe {ruta_datos}. Ejecuten primero las pruebas o usen "
                         "--datos modelo/datos/datos_modelo_EJEMPLO.csv")
    salida = Path(args.salida)
    salida.mkdir(parents=True, exist_ok=True)

    criterios = leer_criterios()
    claves = [c["clave"] for c in criterios]
    alternativas = leer_alternativas(ruta_datos, claves)
    restricciones = leer_restricciones()
    casos = json.loads((DATOS / "casos.json").read_text(encoding="utf-8"))

    titulo("DATOS DE ENTRADA")
    out(f"Archivo: {ruta_datos.name}")
    if "EJEMPLO" in ruta_datos.name.upper():
        out("!!! ATENCION: son datos de EJEMPLO, no usarlos en el informe.")
    tabla(["Alternativa", *[f"{c['nombre']} ({c['unidad']}) {'↑' if c['tipo'] == 'max' else '↓'}" for c in criterios]],
          [[a["nombre"], *[f"{a[k]:g}" for k in claves]] for a in alternativas])

    titulo("PASO 1. PESOS CON EL PROCESO DE JERARQUIA ANALITICA (PJA / AHP)")
    matriz = leer_matriz_ahp(claves)
    pesos_ahp, cr = ahp(matriz, claves, [c["nombre"] for c in criterios], args.ri)

    filas_csv = []
    resumen = []
    base = None
    for caso in casos:
        pesos = pesos_ahp if caso["pesos"] == "ahp" else caso["pesos"]
        if abs(sum(pesos.values()) - 1) > 1e-6:
            raise SystemExit(f"Los pesos del caso {caso['id']} no suman 1")
        restr = [dict(r) for r in restricciones]

        titulo(f"CASO {caso['id']}. {caso['nombre'].upper()}")
        out(caso["descripcion"])
        if "limite" in caso:
            k = caso["limite"]["criterio"]
            r_lim = next(r for r in restr if r["clave"] == k)
            peor = max(a[k] for a in alternativas) if r_lim["operador"] in ("<=", "<") \
                else min(a[k] for a in alternativas)
            r_lim["umbral"] = peor
            out(f"Umbral de {k} cambiado a {peor:g} (valor exacto de la peor alternativa).")
        out("Pesos usados: " + ", ".join(f"{k} = {f(v)}" for k, v in pesos.items()))

        puntajes = evaluar(alternativas, criterios, pesos, restr)
        if caso["id"] == 1:
            base = (puntajes, pesos)
        for pos, (nombre, s, _) in enumerate(puntajes, 1):
            filas_csv.append([caso["id"], caso["nombre"], pos, nombre, round(s, DEC)])
        resumen.append((caso, puntajes))

        if "limite" in caso:
            k = caso["limite"]["criterio"]
            r_lim = next(r for r in restr if r["clave"] == k)
            mas_estricto = [dict(r) for r in restr]
            paso = 0.01
            for r in mas_estricto:
                if r["clave"] == k:
                    r["umbral"] = r_lim["umbral"] - paso if r["operador"] in ("<=", "<") else r_lim["umbral"] + paso
            out(f"\n  Si el umbral se vuelve {paso} mas estricto ({k} {r_lim['operador']} "
                f"{next(r['umbral'] for r in mas_estricto if r['clave'] == k):g}):")
            otro = evaluar(alternativas, criterios, pesos, mas_estricto, detalle=False)
            descartadas = {a["nombre"] for a in alternativas} - {n for n, _, _ in otro}
            out(f"    se descarta: {', '.join(descartadas) or 'ninguna'}")
            for pos, (nombre, s, _) in enumerate(otro, 1):
                out(f"    {pos}. {nombre}: {f(s)}")

    titulo("ANALISIS DE SENSIBILIDAD (sobre el caso base)")
    out("Se varia el peso de un criterio de 0 a 1 y los demas se ajustan en proporcion:")
    out("  w_j(t) = w_j * (1 - t) / (1 - w_k)")
    out("Cada puntaje es una recta: S_i(t) = b_i + (a_i - b_i) * t,  con a_i = r_ik  y  "
        "b_i = suma(w_j * r_ij, j != k) / (1 - w_k)")
    sens = sensibilidad(base[0], criterios, base[1])
    for c in criterios:
        d = sens[c["clave"]]
        if d["cambios"]:
            txt = "; ".join(f"en t = {f(t)} pasa de {a} a {b}" for t, a, b in d["cambios"])
        else:
            txt = "el ganador no cambia para ningun peso"
        out(f"  {c['nombre']} (peso base {f(d['peso_base'])}): {txt}")
    grafica(sens, criterios, salida / "sensibilidad.png")

    costos = DATOS / "costos.json"
    if costos.exists():
        cfg = json.loads(costos.read_text(encoding="utf-8"))
        u, precio = cfg["utilizacion"], cfg["precio_mensual"]
        titulo("DIMENSIONAMIENTO Y COSTO MENSUAL")
        out(f"Servidor: {cfg['servidor']} a ${precio:g}/mes. Utilizacion maxima por servidor: {u:g}.")
        out("n = techo( D / (u * T) )   y   costo = precio * n")
        filas_costo = []
        for D in cfg["demandas"]:
            out(f"\n  Demanda D = {D} peticiones/s:")
            for a in alternativas:
                cap = u * a["throughput"]
                n = math.ceil(D / cap)
                out(f"    {a['nombre']}: {D} / ({u:g} * {a['throughput']:g}) = {D} / {cap:.2f} = {D / cap:.2f}"
                    f"  ->  n = {n}  ->  ${precio * n:g}/mes")
                filas_costo.append([D, a["nombre"], round(cap, 2), n, precio * n])
        with open(salida / "costos_herramienta.csv", "w", newline="", encoding="utf-8") as fh:
            w = csv.writer(fh)
            w.writerow(["demanda_rps", "alternativa", "capacidad_util_rps", "servidores", "costo_mensual_usd"])
            w.writerows(filas_costo)

    titulo("RESUMEN DE LOS CASOS")
    for caso, puntajes in resumen:
        ganador = puntajes[0][0] if puntajes else "ninguno"
        out(f"  Caso {caso['id']} ({caso['nombre']}): gana {ganador}  |  "
            + ", ".join(f"{n} = {f(s)}" for n, s, _ in puntajes))
    out(f"  Razon de consistencia de los pesos AHP: {f(cr)}")

    with open(salida / "puntajes_herramienta.csv", "w", newline="", encoding="utf-8") as fh:
        w = csv.writer(fh)
        w.writerow(["caso", "nombre_caso", "posicion", "alternativa", "puntaje"])
        w.writerows(filas_csv)
    with open(salida / "contrastacion_PLANTILLA.csv", "w", newline="", encoding="utf-8") as fh:
        w = csv.writer(fh)
        w.writerow(["caso", "alternativa", "puntaje_manual", "puntaje_herramienta", "diferencia"])
        for fila in filas_csv:
            w.writerow([fila[0], fila[3], "", fila[4], ""])
    (salida / "salida_modelo.txt").write_text("\n".join(LINEAS), encoding="utf-8")
    print(f"\nArchivos en {salida}: salida_modelo.txt, puntajes_herramienta.csv, "
          "contrastacion_PLANTILLA.csv, sensibilidad.png")


if __name__ == "__main__":
    main()
