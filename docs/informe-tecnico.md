# Asignación de la oficina más cercana por código postal: informe técnico

> Instantánea del 2026-11-25. Los tres gráficos y el mapa no caben en Markdown: esta copia los marca como *[Gráfico: …]*. La versión completa, con gráficos y mapa, está en el documento en línea: https://claude.ai/artifact/A7Xbg2csaA1BKJzZ3KXSUp
>
> **Estado en v0.2.0:** las debilidades 1, 4, 5, 6, 7 y 8 están resueltas; la 2 y la 3 están mitigadas con las opciones `--precision` y `--max-km`, que no cambian la salida por defecto. Queda abierta la distancia real por carretera o por mar (debilidad 3) y la licencia del propio código. El resto del texto es la instantánea del 2026-11-25.

Un script de Python de unas 125 líneas, sin dependencias, asigna a cada código postal (CP) español la oficina más cercana en línea recta. En esta sesión lo endurecimos, construimos unos datos sintéticos que ejercitan todos los casos de entrada que se nos ocurrieron y medimos dónde es frágil.

## Qué hace y cómo funciona

Dada una lista de CPs y otra de oficinas, el script escribe una fila por CP con la oficina más cercana y la distancia en km. Se ejecuta con `python oficina_cercana.py cps.csv oficinas.csv` y el resultado es siempre `asignacion.csv` en el directorio de trabajo.

1. **Coordenadas.** `carga_coordenadas()` lee `ES.txt` de GeoNames (37 867 filas) y construye `{cp: (lat, lon)}`. Si un CP aparece en varias localidades, se promedia. Si falta `ES.txt`, se descarga de GeoNames en la primera ejecución.
2. **Entrada.** `lee_csv()` detecta el delimitador (`;`, `,` o tabulador), quita el BOM y salta la primera fila si su primera celda no es un CP válido (la cabecera).
3. **Normalización.** `normaliza_cp()` es el único lugar donde se limpia un CP: quita espacios y el sufijo `.0` (flotantes de Excel), rellena con ceros hasta cinco dígitos y rechaza lo no numérico.
4. **Emparejamiento.** Para cada CP, `min()` sobre todas las oficinas con la fórmula del haversine (radio terrestre de 6371 km).
5. **Salida.** Un fichero delimitado por `;` en UTF-8 con BOM, para que Excel lo abra directamente. Los CPs sin coordenadas se conservan y se marcan `SIN COORDENADAS` en lugar de descartarse.

El diseño es deliberadamente pequeño: solo biblioteca estándar, sin estado y sin base de datos. Es el tamaño adecuado para un trabajo por lotes puntual, y por eso las debilidades de más abajo son baratas de corregir.

## El algoritmo sobre un mapa

*[Mapa de España: cada CP unido por una línea a su oficina más cercana; las líneas azules superan los 100 km. Cuatro casos numerados. Ver el documento en línea.]*

Cada CP se convierte en un punto con la latitud y la longitud de GeoNames. El script mide la distancia en línea recta a todas las oficinas y une el CP con la más cercana; las líneas azules marcan las asignaciones de más de 100 km. Cuatro casos del mapa muestran las reglas:

1. **Gana la distancia, no el prefijo del CP.** Madrid-Centro y Madrid-Norte están a menos de 10 km entre sí. El CP `28045` queda a 2,8 km de Madrid-Centro y se asigna a ella; `28033` y `28034` quedan más cerca de Madrid-Norte.
2. **Sin oficina en la zona, se asigna la más cercana de todas.** Cádiz (`11004`) no tiene oficina en la provincia y gana Sevilla a 100,1 km. No existe un límite de distancia.
3. **El mar no cuenta.** Arrecife (`35500`) se asigna a Las Palmas a 205,8 km, cruzando mar abierto. Canarias se dibuja aparte y fuera de escala.
4. **Ceuta y Melilla tampoco.** Melilla (`52001`) va a Málaga a 207,3 km y Ceuta (`51001`) a 121,9 km, atravesando el Mediterráneo y el Estrecho.

Los CPs sin coordenadas en GeoNames no aparecen en el mapa: se escriben como `SIN COORDENADAS` y no se asignan a ninguna oficina. Tampoco se dibujan las 13 filas de salida con distancia 0, cuyo CP coincide con el de una oficina, porque quedarían debajo del cuadrado.

## Qué hicimos en esta sesión

Seis bloques de trabajo, en orden. Dos de ellos eran errores encontrados al probar, no al leer.

| # | Cambio | Motivo | Evidencia |
| --- | --- | --- | --- |
| 1 | Escribimos `CLAUDE.md` (arquitectura, comando de ejecución, comportamientos a conservar) | Las sesiones futuras empiezan con el contexto en vez de volver a deducirlo | Fichero en el repo; se mantiene en inglés por decisión |
| 2 | Auditamos los datos sintéticos | Comprobar que los datos de prueba prueban algo | Recalculamos las 12 distancias de forma independiente: coincidieron 12 de 12 |
| 3 | Corregimos el `IndexError` con filas de oficinas de menos de dos columnas | `fila[1]` tumbaba toda la ejecución por una fila mala | La fila `41002` ahora se salta con un aviso |
| 4 | Corregimos el valor de reserva del delimitador en `lee_csv()` | `csv.Sniffer` falla cuando las filas tienen distinto ancho y la reserva era la coma, así que un fichero con `;` se quedaba en una sola columna | Lo encontramos al probar el cambio 3; la primera versión de la corrección modificaba la clase global `csv.excel` y se sustituyó por una subclase |
| 5 | Rehicimos `cps.csv` y `oficinas.csv` | Madrid-Norte nunca ganaba un CP, así que la afirmación «todas las oficinas se ejercitan» era falsa; ningún caso cubría cabeceras, columnas extra ni CPs inválidos | 44 filas de salida, 5 marcadas `SIN COORDENADAS` |
| 6 | `git init`, ramas `main` y `develop`, dos commits y el merge de la rama de datos | El proyecto pasó a ser código real | `2eb27b1` en `main`; `0da198c` integrado en `develop` con `3195ab7` |

La salida de los datos del proyecto es idéntica byte a byte antes y después de las correcciones 3 y 4, así que ninguna cambió el comportamiento con entrada válida.

## Hallazgos medidos

La mitad de los CPs se promedian a partir de varias localidades, y en 131 de ellos el promedio queda a más de 25 km de alguna localidad. Eso es una fuente importante de error, junto con la suposición de línea recta. Todas las cifras salen de `ES.txt` versionado, calculadas el 2026-11-25.

| Medida | Valor |
| --- | --- |
| Filas de `ES.txt` | 37 867 |
| CPs únicos (los 52 prefijos de provincia, del 01 al 52) | 11 150 |
| CPs que abarcan más de una localidad | 5452 (49%) |
| Distancia de una localidad al centroide promediado de su CP: mediana | 1,9 km |
| Igual, percentil 90 | 7,8 km |
| Igual, percentil 99 | 38,7 km |
| Igual, peor caso (CP 14600) | 112,1 km |
| Tiempo de emparejamiento, 11 oficinas, los 11 150 CPs | unos 0,1 s (13 µs por CP) |
| Tiempo de emparejamiento, 1000 oficinas, los 11 150 CPs | unos 12,9 s (1159 µs por CP) |

*[Gráfico: «131 de 5452 CPs multilocalidad tienen una localidad a más de 25 km de su centroide». Distribución por tramos: hasta 1 km: 2036; 1-5 km: 2306; 5-10 km: 749; 10-25 km: 230; más de 25 km: 131.]*

Dos lecturas. Primera: el centroide de un CP es un buen sustituto para un CP urbano típico, pero malo para un CP rural que agrupa pueblos lejanos: un resultado de 1,8 km es fiable; uno de 38 km puede errar en el mismo orden. Segunda: el coste es O(CPs × oficinas) y lineal en oficinas: irrelevante con 11, notable con 1000, y por eso un índice espacial solo compensa a esa escala.

En la ejecución con los datos sintéticos, 13 de los 39 CPs asignados coinciden con el CP de su oficina, y 8 quedan a más de 100 km. Son líneas rectas: Mahón a Palma y Arrecife a Las Palmas cruzan el mar.

*[Gráfico: «8 de 39 CPs asignados quedan a más de 100 km de su oficina». Por tramos: 0 km (mismo CP): 13; 0-5 km: 7; 5-50 km: 5; 50-100 km: 6; 100-200 km: 4; más de 200 km: 4.]*

## Datos sintéticos: matriz de cobertura

`cps.csv` (cabecera, una línea en blanco y 44 filas de CP) y `oficinas.csv` (cabecera y 22 filas de oficinas) son lo bastante pequeños para leerlos a ojo y cubren un caso por grupo de filas. Se usan CPs y coordenadas de GeoNames reales, así que cada distancia es comprobable. La ejecución produce 44 filas de salida, 5 de ellas `SIN COORDENADAS`.

| Caso | Entrada de ejemplo | Comportamiento esperado |
| --- | --- | --- |
| CP sin ceros a la izquierda | `8001`, `1001` | Se rellena a `08001`, `01001` |
| Flotante de Excel | `41002.0`, oficina `18001.0` | Se quita el sufijo |
| Espacios sueltos | ` 46010`, `28013 `, oficina ` 47001 ` | Se recortan |
| Fila de cabecera | `codigo_postal`, `cp;oficina` | Se salta |
| Columna extra | `29600;comentario extra` | Solo se usa la primera columna |
| Línea en blanco | fila vacía | Se ignora |
| CP de entrada duplicado | `28013` dos veces | Una fila de salida por fila de entrada, sin deduplicar |
| CP inválido | `ABC12`, `-28013`, `280130`, `00000` | `SIN COORDENADAS` |
| CP de oficina desconocido | `99999`, `abc` | Oficina descartada con aviso |
| Oficina sin nombre | `41002`, `06001;` | Se salta con aviso (el antiguo `IndexError`) |
| Empate exacto | Sevilla-Duplicada comparte el CP `41002` | Gana el menor CP de oficina y luego el nombre, no el orden del fichero; la perdedora nunca aparece |
| Una oficina gana varios CPs | Madrid-Norte: `28033`, `28034`, `28050` | La más cercana en km, no por prefijo de CP |
| Acentos en nombres | `Oficina Logroño-Centro` | UTF-8 llega intacto a la salida |
| Islas y ciudades autónomas | Mahón, Arrecife, Ceuta, Melilla | Asignadas en línea recta, a través del mar |
| CP promediado | `31700` (seis localidades) | Se usa el centroide |
| Larga distancia | `10001` Cáceres a Sevilla | 233,4 km, sin límite |

Todas las oficinas válidas ganan al menos un CP salvo Sevilla-Duplicada. Esa excepción es intencionada y está documentada en `CLAUDE.md`.

*[Gráfico: «17 de 18 oficinas ganan algún CP; la excepción es Sevilla-Duplicada». CPs por oficina: Sevilla-Casco Antiguo 5, Madrid-Centro 5, Málaga-Centro 5, Logroño-Centro 3, Madrid-Norte 3, Barcelona-Eixample 3, A Coruña-Oliveira 2, Pamplona-Centro 2, Valencia-Ciutat Vella 2, Las Palmas-Centro 2, Bilbao-Abando 1, Zaragoza-Delicias 1, Palma-Centro 1, Valladolid-Centro 1, Murcia-Centro 1, Granada-Centro 1, Zaragoza-Centro 1, Sevilla-Duplicada 0.]*

## Debilidades y riesgos

Ordenadas por la probabilidad de que el problema afecte a datos reales y por lo silencioso que sea. Todas están resueltas o mitigadas y se conservan como registro, con su estado actual en cada fila; la 1 se reprodujo durante esta sesión.

| # | Debilidad | Dónde | Consecuencia |
| --- | --- | --- | --- |
| 1 | **Resuelta en v0.1.0: la primera fila se descartaba en silencio si no era un CP válido.** Un fichero sin cabecera cuya primera fila fuera `ABC12` perdía esa fila sin aviso (reproducido: la salida solo contenía `28013`). Ahora solo se salta una primera celda sin ningún dígito, y `ABC12` sale como `SIN COORDENADAS`. Limitación: una cabecera con dígitos (`cp2`) se lee como dato. | `lee_csv()` | Resuelta: ya no hay pérdida silenciosa |
| 2 | **Mitigada: el error del centroide no se informaba.** Un CP promediado sobre localidades a hasta 112 km recibía la misma precisión que uno de una sola localidad. Ahora `--precision` añade `localidades` y `dispersion_km` a la salida; la asignación en sí no mejora, solo se hace visible. | `carga_coordenadas()` | Mitigada: quien lea el fichero puede descontar los CPs dispersos (opción desactivada por defecto) |
| 3 | **Mitigada: la línea recta ignora mar, montañas y carreteras.** Mahón a Palma y Arrecife a Las Palmas se asignan sin marca; Anso (Huesca, `22728`) va a Pamplona. Ahora `--max-km N` añade la columna `lejos` y no cambia la oficina asignada. La distancia real por carretera o por mar sigue abierta: exige un servicio de rutas y una decisión de producto. | `haversine()` | Mitigada: las asignaciones largas se marcan, pero siguen siendo líneas rectas |
| 4 | **Resuelta: los empates dependían del orden del fichero.** `min()` se quedaba con la primera oficina. Ahora desempata el menor CP de oficina y luego el nombre. | `main()` | Resuelta: resultado reproducible entre exportaciones |
| 5 | **Resuelta: la descarga no tenía tiempo límite ni comprobación de integridad.** Ahora hay un límite de 30 s, el zip debe contener `ES.txt`, el contenido se comprueba y se guarda de forma atómica; si algo falla, el script sale con un mensaje y no deja ningún fichero a medias. GeoNames no publica una suma de verificación, así que la comprobación es de formato, no criptográfica. | `descarga_geonames()` | Resuelta: ya no hay bloqueos ni ficheros truncados en la caché |
| 6 | **Resuelta: la distancia se calculaba dos veces por CP.** Ahora se calcula una vez y se reutiliza para la salida. | `main()` | Resuelta |
| 7 | **Resuelta en v0.1.0: no había pruebas automatizadas.** Los datos de prueba existían, pero nada comparaba la salida con un fichero esperado. Ahora `tests/` (19 tests) compara la salida con el fichero de referencia y los avisos, y cubre las primeras filas sin cabecera, los empates, las dos opciones y la descarga con una red simulada. | repo | Resuelta: las regresiones se detectan con `python3 -m pytest tests/ -q` |
| 8 | **Resuelta para los datos: licencia sin verificar.** `ES.txt` está versionado. El readme de GeoNames, consultado el 2026-11-25, confirma la licencia Creative Commons Attribution 4.0 con crédito a GeoNames y un enlace a www.geonames.org; `NOTICE.md` y el README llevan ya la atribución. La licencia del propio código sigue sin decidirse: es decisión del propietario del repositorio. | raíz del repo | Resuelta para los datos; pendiente la licencia del código |

## Qué podría ser bueno

Las mejoras más baratas corrigen fallos silenciosos y fijan el comportamiento actual. Las caras cambian lo que significa «más cercana» y requieren una decisión de producto, no solo código.

| Oportunidad | Beneficio | Coste y contrapartida |
| --- | --- | --- |
| **Prueba de fichero de referencia** (hecha en v0.1.0: `pytest` ejecuta el script con los datos de prueba y compara `asignacion.csv` con el versionado) | Convierte los casos de la matriz en una red contra regresiones; habría detectado el fallo del delimitador | Resuelto en `tests/test_golden.py`. Hay que regenerar el fichero de referencia a propósito cuando cambie el comportamiento |
| **No descartar la primera fila** (hecho en v0.1.0, sin opciones nuevas) | Eliminó la debilidad 1 | Resuelto con una regla más estricta: solo es cabecera una primera celda sin dígitos. Contrapartida: una cabecera con dígitos se lee como dato |
| **Informar la precisión por CP** (hecho: opción `--precision`) | Permite descontar los 131 CPs con dispersión superior a 25 km | Resuelto como opción desactivada por defecto, así que el contrato de la salida no cambia |
| **Límite y marca** (hecho: opción `--max-km` y columna `lejos`) | Hace visibles Ceuta, Melilla, islas y casos rurales extremos en vez de ocultarlos | El umbral lo fija quien ejecuta; no corrige la asignación en sí |
| **Reserva para CPs sin coordenadas**: usar el centroide de la provincia con los dos primeros dígitos | Menos `SIN COORDENADAS` | Es tosco (decenas de km); debe etiquetarse como estimación y nunca mezclarse en silencio con coincidencias exactas |
| **Las k oficinas más cercanas** (las 2 o 3 primeras) en la salida | Da una alternativa a una persona cuando la primera queda al otro lado del mar | Salida más ancha; la pregunta «cuál es la correcta» pasa al lector |
| **Búsqueda vectorizada o indexada** (`numpy`, o un BallTree con la métrica haversine) | Reduce a una fracción los 12,9 s medidos con 1000 oficinas (no medido aquí) | Añade una dependencia y acaba con la propiedad «solo biblioteca estándar»; no sirve de nada con 11 oficinas |
| **Distancia por carretera o tiempo de viaje** (un servicio de rutas como OSRM u OpenRouteService) | Responde a lo que los usuarios suelen querer decir | Dependencia de red, límites de uso, 11 150 × oficinas peticiones salvo que se use una API de matriz; alcance mucho mayor |
| **Desempate determinista** (hecho: menor CP y luego nombre) | Mismo resultado sea cual sea el orden del CSV | Resuelto; los datos de prueba no cambiaron porque «Casco Antiguo» ordena antes que «Duplicada» |

El proyecto sigue siendo valioso como herramienta pequeña y auditable. La mayor parte de la tabla lo mantiene así: solo la búsqueda vectorizada y la distancia por carretera cambian su naturaleza, y conviene elegirlas por lo que las oficinas necesitan de verdad, no por lo que es técnicamente posible.

## Pasos recomendados

1. **Hecho: `main` incluye todo lo publicado**, con los tags `v0.1.0` a `v0.2.0`.
2. **Hecho en v0.1.0: prueba de fichero de referencia** en `tests/test_golden.py`.
3. **Hecho en v0.1.0: la primera fila ya no se descarta en silencio** (debilidad 1). Solo es cabecera una primera celda sin dígitos.
4. **Hecho: columnas de precisión** (`--precision`: localidades y dispersión en km) para que los 131 CPs por encima de 25 km sean visibles para quien lea el fichero.
5. **Decidir qué debe significar «más cercana» para las oficinas** (línea recta, misma masa de tierra, tiempo de viaje) antes de invertir esfuerzo en indexación o rutas. Esa respuesta decide entre la búsqueda vectorizada, el servicio de rutas y la opción más barata de límite y marca.
6. **Hecho: atribución de GeoNames** en `NOTICE.md` y en el README, con la licencia verificada. Falta decidir la licencia del propio código.

## Fuentes

- Código: `oficina_cercana.py` en el directorio del proyecto (`lee_csv` líneas 98-117, `main` desde la línea 150, emparejamiento en las líneas 184-185; líneas de v0.2.0).
- Datos: códigos postales de España de GeoNames, `https://download.geonames.org/export/zip/ES.zip`, versionados en local como `ES.txt`. Las estadísticas de arriba se calcularon con ese fichero el 2026-11-25. El contorno del mapa viene de Natural Earth 1:50m a través del paquete world-atlas, simplificado; su licencia no se verificó aquí.
- Mediciones: scripts ejecutados en un directorio temporal sobre los ficheros versionados; el escalado usó 2000 CPs y oficinas elegidas al azar (semilla 1) y es orientativo, no un benchmark.
- Licencia de GeoNames: verificada el 2026-11-25 en https://download.geonames.org/export/zip/readme.txt (Creative Commons Attribution 4.0, con crédito a GeoNames y un enlace a www.geonames.org). Sigue sin verificarse la licencia del contorno de Natural Earth.
