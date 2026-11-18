# Cambios

Formato: una sección por versión, la más reciente arriba. Cada entrada dice qué cambia para quien usa la herramienta.

## 2.1.1 · 2026-11-18

- Los `.max` guardados con las primeras versiones de la herramienta (antes de la 1.4) también se abren con sus setups y
  sus mezclas de entorno; al guardar pasan a la clave nueva. Antes solo se convertían los de la 1.4 a la 1.6.

## 2.1.0 · 2026-11-18

- **Layers y Objects: una sola lista para todos los setups.** Las capas y objetos que añades en un setup (con "+" o con
  *fetch*) aparecen en todos los demás con el estado que tienen en la escena en ese momento; desde ahí, cada setup
  guarda sus propias casillas. Así una capa puede estar oculta en un setup y visible en otro sin volver a añadirla.
- Un setup nuevo empieza con toda la lista (y con Layers / Objects encendidos si otro setup los usa).
- Las filas que otro setup tiene pero este aún no fija se ven en cursiva y a medio marcar: no se tocan al aplicar
  (se quedan como las dejó el setup anterior) hasta que marcas una casilla.
- Quitar una fila la quita de la lista de todos los setups.
- Los `.max` guardados antes no cambian al abrirlos: sus listas se juntan solo en pantalla.

## 2.0.0 · 2026-11-13

Primera versión publicada de **OpenScene**.

- Setups de escena dentro del `.max`: cámara, resolución, frames, sol, domo, entorno (varios HDRI/cielos mezclados),
  capas, objetos, luces, xrefs, salida, ajustes de render, render elements, post-producción del VFB (Corona), scripts,
  miniatura, notas y todo.
- **Batch Render** con comprobación previa (cámara que falta, rutas, archivos duplicados, scripts o presets que no
  existen), un fallo no para el lote, tiempo por setup y tiempo restante estimado.
- Salida **`.cxr`** con Corona: render elements y LightMix dentro del mismo archivo.
- **Selector de propiedades** con tablas propias para 3ds Max, Corona, V-Ray, V-Ray GPU y FStorm
  (`tools/props_source.py`).
- Presets de setups y de salida en archivos **`.osp`** (también abre `.smp`).
- Lee y convierte los setups que otro gestor de escenas haya guardado en el `.max` (`external.py`).
- Pensado para escenas grandes: solo lee los objetos que usan los setups, agrupa las ráfagas de eventos y comprime los
  setups grandes dentro del `.max`.
- Instalador `.mzp` (3ds Max 2025+), desinstalador y licencia MIT.
