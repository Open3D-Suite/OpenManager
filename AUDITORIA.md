# Auditoría · OpenScene

Revisión del código completo (≈9 000 líneas: Python/PySide6 + MAXScript): cómo aguanta escenas grandes, los límites
que tiene y las mejoras propuestas, ordenadas por impacto.

> Lo que toca MAXScript y la ventana hay que verlo dentro de 3ds Max: ver la lista del final.

---

## 1. Escenas grandes y Batch Render

### Lo que ya está pensado para escenas grandes
| Punto | Cómo funciona |
|---|---|
| Lectura de la escena | Solo se leen los objetos que usan los setups (`oscn_nodesInfo`); la selección se lee al pulsar "+". No hay tope de objetos. |
| Lecturas al volver a la ventana | Se cronometra cada lectura y el intervalo mínimo es `max(0,8 s; 20 × lo que tardó)`. Si una lectura pasa de 1 s, se avisa en el Listener. |
| Ráfagas de eventos (`#nodeCreated` en un merge de 10 000 nodos) | Solo pasa a Python la primera de cada ráfaga; las demás esperan a la siguiente lectura. |
| Texturas | `oscn_texmaps` recorre los mapas una vez (O(n)). |
| Setups guardados en el `.max` | Si pasan de 32 KB se guardan con zlib + base64: 50 setups × 2 000 capas, de 10 MB a 0,43 MB. |
| Tarjeta Layers | Búsqueda por diccionario; el filtro espera 180 ms a que dejes de escribir. |
| Tarjetas pequeñas | Crecen hasta que cabe su contenido, sin barra de scroll; las que tienen tablas sí la tienen. |

### Batch Render
- **Comprobación previa**: cámara que ya no existe, ruta incompleta, `.cxr` sin Corona, **dos setups que escriben el
  mismo archivo**, script pre/post o preset `.rps` que no existe. Te da la lista y decides si seguir.
- **Un setup que falla no para el lote**: se apunta, sigue con el siguiente y al final sale un resumen con los fallos.
- Tiempo por setup en el Listener, **tiempo restante estimado** en la barra de progreso y tiempo total al acabar.
- Salida **.cxr**: con Corona, los render elements y el LightMix van dentro del archivo (no un `.cxr` por elemento).

---

## 2. Límites

1. **El estado se arrastra de un setup a otro.** Una tarjeta apagada no deja la escena como estaba: se queda como la dejó
   el setup anterior. Si el A oculta una capa y el B tiene Layers apagado, el B se renderiza con esa capa oculta. Es a
   propósito (permite re-renderizar un setup o una región sin tocar el resto), pero conviene tenerlo en cuenta en lotes largos.
2. **Todo va en el hilo principal de Max.** Leer la escena, aplicar setups y hacer previews de HDRI bloquean la UI.
3. **Se aplica con una llamada por cambio.** 2 000 capas × 4 propiedades = 8 000 llamadas pymxs al activar un setup
   (~0,5–1 s). Habría que agruparlas en una sola llamada MAXScript.
4. **`oscn_findMap` / `oscn_findTexmap` recorren `getClassInstances`** en cada cambio de un mapa. Con miles de
   CoronaBitmap, cada propiedad del entorno es un recorrido completo.
5. **`oscn_envMaps` recorre todas las instancias** de 10 clases de bitmap/CC en cada lectura de escena. Es lo que más
   pesa en escenas con miles de texturas.
6. **Sin undo**: aplicar un setup va con `undo off`. Ctrl+Z no lo deshace.
7. **Render Elements solo con Corona/Redshift/FStorm** (renombrado `nombre_elemento.ext`). Los canales separados de V-Ray
   (VRayRawImage / *Separate render channels*) no se tocan.
8. **Time Output cambia el `animationRange`** de la escena de forma permanente.
9. **Previews de HDRI**: `openBitmap` de un HDRI de 60 MB congela Max unos segundos por archivo (es automático hasta 60 MB).

---

## 3. Mejoras y complementos propuestos

### Prioridad alta
1. **"Estado base" opcional**: guardar una vez el estado de capas, luces, entorno y render, y restaurarlo antes de cada
   setup del batch ("reset entre setups"), sin quitar el comportamiento actual.
2. **Aplicar en una sola llamada**: mandar la lista de acciones como JSON a una función MAXScript `oscn_applyBatch`.
   Mucho más rápido con muchas capas u objetos.
3. **Caché de mapas por nombre** en MAXScript (diccionario clase|nombre → mapa, que se vacía con los eventos de escena)
   para `oscn_findMap`.
4. **Log de render a disco** (`OpenScene_logs/fecha.txt`): setup, ruta, tiempo, error. Útil para granjas y para
   repasar por la mañana.
5. **Guardar el `.max` antes del batch** y congelar el redibujado de los visores mientras se aplica un setup.

### Prioridad media
6. **Diferencias entre setups**: elegir dos y ver qué cambia (cámara, capas, propiedades).
7. **Token `Frame`/`Pass`** y **subcarpeta por setup** en Render Output. Y una opción **JPG + CXR**: guardar a la vez
   el beauty en jpg y el CXR multicapa.
8. **Enviar a Deadline / Backburner**: un job por setup con su `.max` horneado (Bake ya genera los `.max`).
9. **Búsqueda y filtro en la lista de setups** (por nombre, cámara, estado #WIP/#OK) y **grupos o carpetas** de setups.
10. **Estado/etiqueta en la lista** (`status` ya existe en el modelo pero no se ve): WIP, Review, Final.
11. **Undo de "aplicar setup"**: guardar el estado anterior y poder volver con un botón.
12. **Canales de V-Ray**: poner la ruta de *Separate render channels* y de VRayRawImage con el mismo token.

### Pequeñas
13. Contador de frames total del batch y estimación según el último tiempo por frame.
14. Avisar si el disco de salida tiene poco espacio antes de empezar.
15. Exportar o importar el **layout de tarjetas** para compartirlo con el equipo.
16. Tests automáticos de `model.py` (es Python puro): `final_path`, `external.convert`, `encode/decode`, `parse_frame_list`.

---

## 4. Qué probar en 3ds Max

1. **CXR**: Corona + elementos (LightMix, Z-depth…) y token Extension `.cxr`. Renderizar un setup: **un solo `.cxr`**,
   sin archivos sueltos por elemento, que se abre en Corona Image Editor con todas las capas.
2. CXR con V-Ray activo: la ruta sale en naranja y la comprobación previa avisa.
3. **Barras**: abrir sin setup activo; ninguna tarjeta pequeña (Time Output, Resolution, Scene Name, Dome…) debe
   tener barra vertical. Cambiar Time Output entre Single, Range y List.
4. Escena con más de 5 000 objetos: añadir a Objects un objeto creado al final; no debe salir *(missing)*.
5. Hacer merge de una escena grande con la ventana abierta: no debe congelarse más que el merge.
6. Batch con un setup roto (una ruta de script que no existe…): el lote sigue y al final sale el resumen.
7. Guardar y volver a abrir un `.max` con muchos setups o capas: se leen bien (comprimidos).
8. **Un `.max` con setups de antes de la 2.0.0**: se abren con sus setups y sus mezclas de entorno; al guardar y volver
   a abrir siguen ahí (ya con la clave nueva).
