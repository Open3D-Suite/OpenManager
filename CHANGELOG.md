# Cambios

Formato: una sección por versión, la más reciente arriba. Cada entrada dice qué cambia para quien usa la herramienta.

## 2.2.2 · 2026-11-19

- **El instalador vuelve a funcionar**: el de la 2.2.0 y la 2.2.1 se paraba nada más arrastrarlo con el error
  *"Syntax error: at at, expected name"* (usaba como nombre de variable una palabra que MAXScript tiene reservada) y no
  instalaba nada. Si te salió ese error, arrastra el `OpenScene.mzp` nuevo y listo.
- Antes de generar el `.mzp` se revisan los archivos MAXScript, para que un error así no vuelva a llegar a un paquete.

## 2.2.1 · 2026-11-19

- **Entorno con un Color Correct encima del HDRI**: ya no sale un fondo de otro color (amarillo, por ejemplo) al
  elegirlo en OpenScene. Cuando varios mapas tienen el mismo nombre (mapas que se llaman como su clase, modelos
  importados de otros archivos, copias), OpenScene podía coger el Color Correct de un material en lugar del que está
  sobre el HDRI. Ahora elige siempre el que tiene el HDRI o el cielo debajo, y los ajustes del HDRI (rotación,
  archivo...) tampoco van a parar a un bitmap de un material con el mismo nombre.
- El repositorio está ahora en `github.com/daniellopezcastellanos/OpenScene`.

## 2.2.0 · 2026-11-18

- **El instalador pone el botón en la barra de herramientas**: crea una barra **OpenScene** con el botón, lista para
  arrastrarla a donde quieras. Si ya tienes el botón en alguna barra, no añade otra. Antes de tocar la interfaz guarda
  una copia (`.cuix.before-openscene`) y, si algo falla, la vuelve a poner.
- El desinstalador quita esa barra (las barras propias en las que hayas puesto el botón no se tocan).

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
