# OpenScene

Gestor de *setups* (estados de escena) y render por lotes que vive **dentro de 3ds Max 2025+**
(Python + PySide6 que ya trae Max, más una librería MAXScript). Sin programas aparte ni navegador.

Un **setup** guarda, para un mismo `.max`: cámara, resolución, frames, sol, domo, entorno, capas, objetos,
luces, xrefs, ruta de salida, ajustes de render, post-producción del VFB (Corona) y más. Al clicar un setup
se aplica a la escena; el **Batch Render** (la tetera) renderiza todos los marcados.

Versión **2.1.1** · probado en 3ds Max 2026.3 con Corona 14 (V-Ray / FStorm: tablas incluidas, menos probados).

## Instalar

1. Descarga **`OpenScene.mzp`** y arrástralo a un visor de 3ds Max.
2. *Customize > Customize User Interface > Toolbars*, **Group: Main UI**, **Category: OpenScene**:
   arrastra **OpenScene** a una barra o un menú.

Para quitarlo: *Scripting > Run Script…* > `uninstall.ms` y reinicia Max. Los setups guardados en los
`.max` no se tocan.

- Los setups se guardan **dentro del .max** (atributo de `rootNode`).
- Si un `.max` trae setups guardados por otro gestor de escenas, OpenScene los lee y los convierte; desde que el archivo
  se guarda con los suyos, ya no se pregunta más.
- Presets de setups y de salida: archivos `.osp` (también se abren los `.smp` exportados antes).
- Ajustes de la ventana: `plugcfg\OpenScene.json`.

## Módulos

Scene Name, Camera, Resolution, Time Output, Sun (varios soles/Daylights en pestañas), Lights,
HDRI Browser, Environment (varios HDRI/cielos mezclados como un LightMix), Dome, Background,
Atmosphere, Layers, Objects, XRef Scenes, Variants, Render Output, Render Settings, Render Override, Render Preset,
Render Elements, Post-Production / VFB (Corona), Script File, Script Editor, Thumbnail, Todo y Notes.
Cada ajuste se elige en el **Selector de propiedades** y tiene un lápiz para tomar el valor de la escena.

- **Layers y Objects comparten la lista entre setups**: lo que añades en uno aparece en todos, y cada setup guarda
  sus propias casillas (oculto en uno, visible en otro). Una fila a medio marcar es de la lista pero ese setup aún no
  la fija; al marcarla, se fija. Quitar una fila la quita de todos.
- **Doble clic en la barra de color** de una tarjeta: se pliega y queda solo la barra; otro doble clic la despliega al tamaño que tenía.
- **Tamaño de iconos** (la tuerca > Theme > Icon Size): pequeño, mediano (recomendado) o grande; se aplica al momento.

## Compilar el .mzp

```
python tools/build.py
```

Python 3 normal, sin dependencias. Dibuja los iconos (`package/icons/`) y rehace `OpenScene.mzp`.
`python tools/make_props.py` regenera `props.json` (la tabla del Selector de propiedades) desde `tools/props_source.py`:
ahí están, para cada motor, los ajustes que ofrece cada tarjeta, con sus nombres, rangos y valores por defecto.

Para probar cambios sin reinstalar: copia `package/OpenScene/` sobre la instalada
(`scripts\OpenScene`) y en el Listener de Python: `import openscene; openscene.reload_package()`.

## Estructura

| ruta | qué es |
|---|---|
| `OpenScene.mzp` | el instalador ya compilado |
| `uninstall.ms` | desinstalador |
| `LICENSE` | licencia MIT (va también dentro del .mzp) |
| `CHANGELOG.md` | qué cambia en cada versión |
| `CLAUDE.md` | notas para trabajar en el código con Claude |
| `package/install.ms`, `mzp.run`, `OpenScene.mcr` | instalador y botón de Max |
| `package/OpenScene/openscene_core.ms` | funciones MAXScript que leen y cambian la escena |
| `package/OpenScene/OpenScene_startup.ms` | aviso al abrir un `.max` con setups de otro gestor, para convertirlos |
| `package/OpenScene/openscene/` | la ventana (Python): `window.py`, tarjetas en `cards.py` / `cards2.py`, `maxlink.py` (setup → cambios en Max), `model.py` (datos, sin Max ni Qt), `external.py` (lee los setups de otro gestor, opcional) |
| `tools/` | `build.py` (genera el .mzp), `props_source.py` + `make_props.py` (generan `props.json`) |

## Si algo falla

Copia lo que salga en el **MAXScript Listener** (F11): los errores llevan el prefijo `OpenScene`.

## Límites

- Post-Production / VFB solo con Corona.
- Salida **.cxr** (Render Output): solo con Corona. Los render elements y el LightMix van dentro del .cxr, así que no se
  guarda un archivo aparte por elemento. Con otro motor la ruta se marca en naranja y no se guarda.
- Los setups grandes se guardan comprimidos en el .max.
- Ver `AUDITORIA.md` para los límites con escenas grandes y las mejoras pendientes.

## Licencia y marcas

[MIT](LICENSE) © 2026 Daniel Castellanos. Puedes usarlo, modificarlo y redistribuirlo, también en proyectos
comerciales, siempre que mantengas el aviso de copyright y la licencia. Se ofrece tal cual, sin garantías.

OpenScene es un proyecto independiente: no está afiliado, patrocinado ni respaldado por Autodesk, Chaos ni ningún otro
fabricante. 3ds Max es una marca de Autodesk, Inc.; Corona y V-Ray son marcas de Chaos Software; FStorm, Redshift,
Arnold y el resto de nombres de productos pertenecen a sus dueños y se citan solo para indicar con qué funciona.
Los iconos de la interfaz se dibujan en tiempo de ejecución con la fuente de símbolos que trae Windows (no se
redistribuye) y con formas propias.
