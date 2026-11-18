# Proyecto Final IO – Selección del lenguaje de backend (U.1)

**Universidad Técnica de Ambato · FISEI · Investigación Operativa**

Equipo: Santiago Alejandro Gamboa Araujo · Sheyla Eliana Pacha Lucintuña ·
Martín Sebastián Palacios Vaca · David Alexander Pérez Alvarez

**Resultado:** Python (FastAPI) queda fuera por la restricción de latencia (p95 = 636 ms > 300 ms);
C# (.NET) obtiene el mayor puntaje (0.9186) frente a Node.js (Express) (0.7454). La decisión solo
cambiaría si el peso de la memoria RAM superara 0.4488.

| Contenido | Dónde |
|---|---|
| Informe (APA 7) | `Informe_Proyecto_Final_IO.docx` |
| Calculadora (abrir en el navegador) | `calculadora/index.html` |
| Modelo de decisión (Python) | `modelo/modelo_decision.py` → `modelo/salidas/` |
| Mediciones (30 pruebas + 10 de Python con 2 procesos) | `resultados/` |
| Respuestas de la encuesta AHP (anónimas) | `Importancia de criterios para elegir el lenguaje de backend.csv/` |

---

Kit completo para medir tres APIs equivalentes y aplicar el modelo de decisión
multicriterio ponderado (PJA/AHP + puntaje global + sensibilidad).

| Alternativa | Carpeta | Puerto en tu PC |
|---|---|---|
| Python (FastAPI) | `apis/python-fastapi` | 8001 |
| Node.js (Express) | `apis/node-express` | 8002 |
| C# (.NET 8 Minimal API) | `apis/csharp-dotnet` | 8003 |

Las tres tienen los mismos endpoints, la misma base de datos (PostgreSQL) y los mismos límites
(1 CPU y 512 MB cada una):

| Endpoint | Qué hace | Qué mide |
|---|---|---|
| `GET /items?limit=100` | Lista los últimos 100 registros | Lectura de base de datos |
| `POST /items` | Inserta un registro `{"name": "...", "price": 12.5}` | Escritura |
| `GET /primes?n=20000` | Cuenta los primos hasta n (mismo algoritmo en los 3) | Cálculo de CPU |
| `GET /health` | Responde `{"status":"ok"}` | Solo para saber si la API está lista |

---

## 1. Requisitos (una sola vez)

- **Docker Desktop** abierto (en Windows con WSL 2).
- **Git Bash** (Windows) o una terminal en Linux/macOS.
- **Python 3** con matplotlib: `pip install matplotlib`

No hace falta instalar Python, Node ni .NET para las APIs ni k6: todo corre dentro de Docker.

---

## 2. Ejecutar las pruebas de carga

En Git Bash, dentro de la carpeta del proyecto:

```bash
# Prueba rapida para ver que todo funciona (unos 3 minutos)
REPS=1 DURATION=15s WARMUP=5s bash scripts/ejecutar_pruebas.sh

# Medicion oficial: 10 repeticiones x 3 lenguajes x (15 s + 60 s) ≈ 45 minutos
bash scripts/ejecutar_pruebas.sh
```

Qué hace en cada repetición y para cada lenguaje:
1. Restablece la base de datos a los mismos 1000 registros.
2. Reinicia la API (memoria limpia).
3. Calentamiento de 15 s (no se guarda).
4. Prueba de 60 s con 50 usuarios simultáneos (k6): por cada 10 peticiones, 7 lecturas, 2 escrituras y 1 cálculo.
5. Mientras tanto, guarda CPU y RAM con `docker stats`.

Los lenguajes se alternan en cada repetición (Python, Node, C#, Python, Node, C#…)
para que ningún lenguaje se beneficie de que la PC esté más fresca o más caliente.

**Durante la medición no usen la PC para otra cosa** (cierren el navegador, juegos, etc.).

### Resultados

| Archivo | Contenido | Dónde va en el informe |
|---|---|---|
| `resultados/raw/` | Datos crudos de k6 y docker stats | Anexos |
| `resultados/mediciones.csv` | Una fila por repetición | Anexos |
| `resultados/resumen.csv` | Promedio y desviación estándar | Resultados |
| `resultados/entorno.txt` | Versiones y especificaciones del equipo | Metodología |
| `modelo/datos/datos_modelo.csv` | Tabla de entrada del modelo | Desarrollo |

Si se usan varias PC, **todas las mediciones oficiales deben hacerse en la misma**.

---

## 3. Datos que tienen que poner ustedes

### a) Popularidad del framework → `modelo/datos/popularidad.csv`
Ya viene lleno con el porcentaje de uso de la **Stack Overflow Developer Survey 2025**
(sección *Web frameworks and technologies*, todos los encuestados):
FastAPI 14.8 %, Express 19.9 % y ASP.NET Core 19.7 %. Se maximiza.
Fuente: https://survey.stackoverflow.co/2025/technology/
Antes de entregar, entren a la página y confirmen los números.

### b) Pesos AHP → encuesta
1. Copien `modelo/datos/ahp_respuestas_PLANTILLA.csv` como `modelo/datos/ahp_respuestas.csv`.
2. Cada persona responde las 15 comparaciones con la escala de Saaty:
   `"¿Qué tan importante es criterio_a frente a criterio_b?"`

   | Valor | Significado |
   |---|---|
   | 1 | Igual de importantes |
   | 3 | criterio_a moderadamente más importante |
   | 5 | criterio_a fuertemente más importante |
   | 7 | muy fuertemente |
   | 9 | extremadamente |
   | 1/3, 1/5… | Al revés: criterio_b es más importante |

3. Una persona = 15 filas (P1, P2, P3…). El script une todas las respuestas con la **media geométrica**.

Si no existe `ahp_respuestas.csv`, el modelo usa `modelo/datos/ahp_matriz.csv` (que trae una matriz de ejemplo).

### c) Restricciones duras → `modelo/datos/restricciones.csv`
Vienen latencia p95 ≤ 300 ms y tasa de error ≤ 1 %. Pueden cambiar los umbrales, pero justifíquenlos.

---

## 4. Ejecutar el modelo

```bash
python modelo/modelo_decision.py
```

Para probarlo antes de tener datos reales:
```bash
python modelo/modelo_decision.py --datos modelo/datos/datos_modelo_EJEMPLO.csv
```

Imprime **cada operación** (igual que se hace a mano) y guarda en `modelo/salidas/`:

| Archivo | Para qué |
|---|---|
| `salida_modelo.txt` | Todo el procedimiento: AHP, filtro, normalización, puntajes y casos |
| `puntajes_herramienta.csv` | Puntajes de cada caso |
| `contrastacion_PLANTILLA.csv` | Tabla del paso 6: llenan la columna del cálculo manual y la diferencia |
| `sensibilidad.png` | Gráfica con los pesos críticos donde cambia el ganador |

Los 4 casos de prueba están en `modelo/datos/casos.json`:
1. **Base** – pesos AHP.
2. **Prioridad en rendimiento** – suben throughput y latencia.
3. **Prioridad en productividad** – suben líneas de código y popularidad del framework.
4. **Caso límite** – el umbral de latencia queda exactamente en el valor del lenguaje más lento
   (cumple por estar en el límite) y se muestra qué pasa si el umbral baja 0.01 ms.

### Razón de consistencia
Por defecto usa el índice aleatorio del libro de Taha, `IA = 1.98(n − 2)/n`.
Para usar la tabla de Saaty: `python modelo/modelo_decision.py --ri saaty`.
Comprueben con el ejemplo resuelto del libro que obtienen los mismos números.

---

## 5. Solución manual (paso 3 del proyecto)

Hagan a mano, con 4 decimales, los mismos pasos que imprime el script para el **caso base**:
matriz AHP → suma de columnas → normalizada → pesos → RC → filtro → normalización → puntajes.
Luego llenen `contrastacion_PLANTILLA.csv`. Las diferencias deberían ser de redondeo (≤ 0.001).

---

## 6. Puntos para el análisis crítico

- **CPU:** con carga máxima y 1 CPU por API, las tres pueden quedar cerca del 100 % y el criterio casi
  no diferencia. Si pasa, explíquenlo y consideren usar CPU por cada 1000 peticiones.
- **La normalización depende del conjunto:** en el caso límite, al salir un lenguaje cambian el máximo y
  el mínimo, y con ellos los puntajes de los demás.
- **Empate técnico:** si la diferencia entre dos lenguajes es menor que su desviación estándar
  (`resumen.csv`), la medición no permite separarlos.
- **Líneas de código** mide el tamaño del código, no el esfuerzo real de programar.
- Las mediciones valen para **esta PC y esta API pequeña**; en otra máquina los valores cambian.

---

## 7. Declaración de uso de IA (va al final de los Anexos)

Las APIs, los scripts de medición y el script del modelo se generaron con apoyo de una herramienta de
IA generativa. Declárenlo indicando la herramienta, el propósito (generar el código de las APIs y de los
scripts) y la parte del trabajo. Por eso el criterio "esfuerzo de desarrollo en horas" se reemplazó por
"líneas de código". El modelo, la solución manual y el análisis crítico deben ser de ustedes.
