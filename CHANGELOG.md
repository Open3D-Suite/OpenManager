# Cambios

Formato: una sección por versión, la más reciente arriba. Cada entrada dice qué cambia para quien usa la herramienta.

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
