# Encuesta AHP para Google Forms

## Título del formulario

Importancia de criterios para elegir el lenguaje de backend

## Descripción del formulario

Somos estudiantes de Ingeniería de Software de la FISEI (UTA). En el proyecto final de
Investigación Operativa comparamos tres lenguajes para desarrollar el backend de una
aplicación web típica: Python (FastAPI), Node.js (Express) y C# (.NET).

Necesitamos saber qué criterios consideras más importantes. En cada pregunta compara
dos criterios y elige cuál importa más y cuánto más. No hay respuestas correctas.
Toma unos 5 minutos y es anónima.

Significado de los criterios:
- Throughput: cuántas peticiones por segundo puede atender la API.
- Latencia: cuánto tarda la API en responder.
- Memoria RAM: cuánta memoria consume el servidor.
- CPU: cuánto procesador consume el servidor.
- Líneas de código: cuánto código hay que escribir para hacer lo mismo.
- Popularidad: cuántos desarrolladores usan el framework (más ejemplos y ayuda en internet).

---

## Pregunta inicial (opcional)

**¿En qué semestre estás?** → tipo *Respuesta corta*, no obligatoria.

---

## Las 15 preguntas de comparación

Todas son tipo **Opción múltiple**, **obligatorias**, y con **las mismas 9 opciones**.
Crea la primera, cópiala con el botón "Duplicar" y solo cambia el título.

### Opciones (iguales en las 15 preguntas, en este orden)

1. La primera es extremadamente más importante (9)
2. La primera es muy fuertemente más importante (7)
3. La primera es fuertemente más importante (5)
4. La primera es moderadamente más importante (3)
5. Ambas son igual de importantes (1)
6. La segunda es moderadamente más importante (1/3)
7. La segunda es fuertemente más importante (1/5)
8. La segunda es muy fuertemente más importante (1/7)
9. La segunda es extremadamente más importante (1/9)

**Importante:** no borres el número entre paréntesis del final; el script lo usa para leer la respuesta.

### Títulos de las preguntas (en este orden exacto)

1. Throughput vs. Latencia
2. Throughput vs. Memoria RAM
3. Throughput vs. CPU
4. Throughput vs. Líneas de código
5. Throughput vs. Popularidad
6. Latencia vs. Memoria RAM
7. Latencia vs. CPU
8. Latencia vs. Líneas de código
9. Latencia vs. Popularidad
10. Memoria RAM vs. CPU
11. Memoria RAM vs. Líneas de código
12. Memoria RAM vs. Popularidad
13. CPU vs. Líneas de código
14. CPU vs. Popularidad
15. Líneas de código vs. Popularidad

En cada una, "la primera" es el criterio que va antes del "vs." y "la segunda" el que va después.

---

## Después de recoger las respuestas

1. En Google Forms: pestaña **Respuestas** → los tres puntos → **Descargar respuestas (.csv)**.
2. Descomprime el archivo y guarda el `.csv` en la carpeta `io-backend`.
3. En Git Bash, dentro de `io-backend`:

```bash
python scripts/convertir_encuesta.py "nombre_del_archivo.csv" --excluir-inconsistentes
python modelo/modelo_decision.py
```

El primer comando muestra la razón de consistencia (RC) de cada persona. Quien tenga
RC ≥ 0.10 respondió de forma contradictoria y se excluye. Guarden esa tabla para los Anexos.
