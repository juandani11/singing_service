# PROMPT — Agente Figma: Prototipo SyncDance · Módulo de Canto (Análisis vocal)

> **Entrega:** pega estos 3 bloques SEPARADOS (uno por mensaje) al agente Figma.
> Si el agente no tiene las skills `figma-generate-design`/`figma-use`, no importa: el flujo completo está inline en el Bloque 3.
>
> **Actualización (2ª revisión de `prototipo.png`):** el **BLOQUE 4 se aplicó** —
> la pantalla principal ya tiene todas las secciones (Segmentos 3 filas,
> Feedback 2 cards, Evaluación combinada, CTA, nota bajo la curva) y ya no hay
> huérfanos visibles. Pendiente sólo el pulido: **usa BLOQUE 5 y BLOQUE 6**
> (iconos de nav, verificación estructural, validación final y reporte).

---

## BLOQUE 1 — Contexto y requisitos

```
CONTEXTO — SyncDance AI · Módulo de CANTO (área de análisis vocal)

Objetivo: crear en Figma la primera pantalla del módulo de Canto del prototipo
SyncDance: layout base de análisis vocal (danza y canto) para app móvil.

Producto: plataforma de evaluación técnica de baile con visión artificial + expansión
de análisis vocal. Stack: Django/DRF (backend), Angular (web), FLUTTER (app móvil →
Material Design), PostgreSQL, Redis+Celery (workers de IA).

Área de canto = Épica EP-08 "Análisis vocal multimodal":
- RF-37 Extracción de pitch: curva F0/pitch del audio del alumno y de la referencia.
- RF-38 Evaluación de afinación: comparar pitch alumno vs. referencia → puntaje/errores.
- RF-39 Feedback vocal: segmentos desafinados + recomendaciones básicas.
- RF-40 Puntaje multimodal: combinar baile y canto en evaluación compuesta (ponderación).

Historias de usuario (Backlog, Sprint 5, P2):
- HU-43: el sistema obtiene la curva de frecuencia fundamental (F0) del audio del
  alumno y distingue segmentos sin voz de notas desafinadas.
- HU-44: alineación temporal de pitch alumno ↔ referencia (tolera desfases pequeños
  de inicio).
- HU-45: mide la diferencia de pitch por segmento (cents/tono), identifica segmentos
  desafinados con timestamp y produce un score vocal de 0 a 100 documentado.
- HU-46: el alumno ve el score vocal y los segmentos/momentos con mayor desviación;
  los mensajes diferencian explícitamente la AUSENCIA DE VOZ de la DESAFINACIÓN.
- HU-47: resultado combinado baile + canto (solo si ambas modalidades están
  disponibles; los scores individuales siguen visibles; ponderaciones documentadas).

Flujo de referencia: alumno graba intento → workers extraen audio → extracción de
pitch → alineación con referencia → comparación por segmento → puntaje + feedback →
visualización en app.

ARCHIVO FIGMA:
- fileKey: xq0uCROdEaMo3wu4WLFgB7
- Página: Page 1 (id 0:1), actualmente vacía (o con la pantalla "01" de otro agente;
  si existe, colócate a su derecha con x = maxX + 200).
- Tu pantalla: nombre EXACTO "02 · Canto — Análisis vocal", tamaño 412 × 915 (M3 phone).
```

---

## BLOQUE 2 — Design system (reutilizar, NO repetir investigación)

```
DESIGN SYSTEM YA INVESTIGADO — úsalo tal cual.

LIBRERÍA: "Material 3 Design Kit" (comunidad).
1. Antes de construir: habilitar la librería en el archivo → panel Assets →
   Libraries (Browse libraries) → buscar "Material 3 Design Kit" → Add/Enable.
   Si no se puede habilitar, importar por key:
   figma.importComponentSetByKeyAsync(key) / importStyleByKeyAsync(key).
   NOTA: las variantes "Label only" de tabs NO existen en el kit → usa chips de texto
   o componentes locales (ver Bloque 3).
2. Tipografía del producto: ROBOTO (Regular/Medium/Bold). Nunca Inter.
   Cargar fuentes antes de mutar texto (para texto dentro de instancias, obtener fuentes
   con getStyledTextSegments(['fontName'])).

COMPONENTES (figma.importComponentSetByKeyAsync):
| Componente | componentSetKey | Props/variantes |
| App bar | 23a20484e255cb14cf467ccc984ac918e457cefb | Configuration=Small, Elevation=Flat; booleans Show 1st/2nd/3rd trailing action. El título NO tiene prop → override de TEXT anidado. |
| Primary tabs | 94e100e3db494a412e33829f9d81d34b460e09dc | Label text#53409:27 (TEXT), Selected=True/False |
| Button | ab924dce8b851fd820bd0d56da24a9c489311ae6 | Label text#58653:0 (TEXT), Show icon#58653:51 (BOOLEAN), Type=Round/Square, Size=XSmall..XLarge, State=Enabled |
| Filter chip | a3c83c534d78babd0613f4f14c72ac25ebae90cf | Label text#53923:200 (TEXT), Selected, Style=Outlined/Elevated |
| Stacked card | a79bb6c8ccfee2be2b9d5cefcb81fc2d88c62fff | Header text#58710:21, Title text#58710:35, Subtitle text#58710:42, Supporting text#58710:49, Subhead text#58710:28; Style=Filled/Elevated/Outlined |
| List item | e51596a48a52120d41c1a8260b43e27018e3d4bb | Content#59340:24 es SLOT (difícil vía API) → preferir componente local para filas custom |
| Navigation Bar: Vertical items | d044e5ea85ee8d7479269dc54c5cb55b7156821d | Nav items=3/4/5; labels por override de TEXT anidados |

VARIABLES DE COLOR (figma.variables.importVariableByKeyAsync + setBoundVariableForPaint):
| Variable | key |
| Schemes/Surface | eb6111c4a47968bf3cead35c6052873423b4d3d5 |
| Schemes/Primary | 76bfbbf87c5f600256e614f12eaf0699927c5a35 |
| Schemes/On Primary | 43e2fa808c95da8ac12fd3eddae33367c25249ed |
| Schemes/Primary Container | a103186b128f8b374dd67aca273d14b16f80c015 |
| Schemes/On Primary Container | 3955ea91dec6375cafc103197d010e8f972b48ea |
| Schemes/On Surface | d708be20513001c4083ed24c1e58c2fdaca456b3 |
| Schemes/On Surface Variant | 2669a52b8e7217f9819767cb22af92e9332d8148 |
| Schemes/Surface Container | 39429ef475465b43ef4cb71db29f18b87b4abf4a |
| Schemes/Surface Container Low | 6617aba8d57dd26a9ead2bd7e7be9f1f1c5c1e6f |
| Schemes/Surface Container High | 872c33cf92cb21916b7722c15fe794eefc5a6e8b |
| Schemes/Surface Container Highest | be8b93f1dc842e52d303a3eca288de51a8df8896 |
| Schemes/Surface Container Lowest | 084fd9eef53493f628f937becb5914405009aa93 |
| Schemes/Secondary Container | f5a5418067dd181a126299ff0ab3ebda1692869b |
| Schemes/On Secondary Container | ef0a1bd6499959dda47dde7449042f0ca0e34ac8 |
| Schemes/Outline | fe6df42091f941865aeced3d5f5fd1477728bbcc |
| Schemes/Outline Variant | 62f3600b56f0544c7c806efc996e3a710e7c4314 |
| Schemes/Error | e1a47274c0e369e5d527533bc0639058333d3894 |
| Schemes/Error Container | a9c06f50afc38482ae08829d2a95f39c0e7bf743 |
| Schemes/On Error Container | 1221ffb0a3af163e60f2f5ef754b971dfeb75dda |
| Schemes/Tertiary Container | 4119db39b5fbdf71ebb1489b47b91fadc6988f42 |
| Schemes/On Tertiary Container | 07b64fedfe13bf11e3fa823ef7b73adbaa4a241c |

FALLBACK DE COLOR — si las variables NO cargan, usar estos hex M3 baseline directos:
Primary #6750A4 · On Primary #FFFFFF · Primary Container #EADDFF · On Primary
Container #21005D · Surface #FFFBFE · On Surface #1C1B1F · On Surface Variant
#49454F · Surface Container Lowest #FFFFFF · Surface Container Low #F7F2FA ·
Surface Container #F3EDF7 · Surface Container High #ECE6F0 · Surface Container
Highest #E6E0E9 · Secondary Container #E8DEF8 · On Secondary Container #1D192B ·
Outline #79747E · Outline Variant #CAC4D0 · Error #B3261E · Error Container
#F9DEDC · On Error Container #410E0B · Tertiary Container #FFD8E4 · On Tertiary
Container #31111D.

ESTILOS DE TEXTO (figma.importStyleByKeyAsync, aplicar con textStyleId):
| M3/headline/large | 6bbad1b27fe05ecdb1858533b6a345777d20d506 |
| M3/headline/large-emphasized | 963d816bfcff983c910426e3bf7ab52b985e78b7 |
| M3/headline/medium | 2b0fde8456dd95575d375d05490a1183fbfbcdb6 |
| M3/headline/medium-emphasized | 786da65add773e921c3fa156e41166c8c227abb8 |
| M3/headline/small | 559680d3555f8c597388270a775e59a3f3b3e9ec |
| M3/headline/small-emphasized | fe7c5ced2203f5b491c7ca41d4bc38ddea9a9cbc |
Si faltan estilos de body/title/label: buscar en la librería "body", "title", "label";
si no, usar Roboto con tamaños M3: body 14/20, body-medium 14/20, title 16/24,
title-medium 16/24, label 12/16, label-large 14/20.
```

---

## BLOQUE 3 — Pantalla, estados, workflow y validación

```
PANTALLA "02 · Canto — Análisis vocal" (412 × 915, vertical, fondo Surface,
clipsContent) — estructura de arriba a abajo con auto-layout:

1. App bar: instancia Configuration=Small, Elevation=Flat; título override
   "Análisis de canto"; 1 acción trailing.
2. Cabecera del intento (padding 16): título "Reggaetón Básico — voz"
   (headline/small-emphasized); meta "Intento #2 · 28 sep 2026" (On Surface
   Variant); chip Filter "Completado".
3. Tabs: fila con 2 tabs/segmentos de igual ancho (cada uno FILL): "Danza"
   (Selected=False) y "Canto" (Selected=True); separador inferior 1px Outline
   Variant. Si Primary tabs/Label only no está en la librería, crear componente
   local de 2 segmentos con mismo estilo M3 (active: texto Primary + subrayado
   3px Primary; inactive: texto On Surface Variant).
4. CARD "Puntaje vocal" (fill Surface Container Lowest, radio 12, stroke Outline
   Variant, padding 16, gap 16):
   a) Fila: anillo de progreso 96×96 (frame con 2 elipses: track Surface
      Container High + arco Primary vía arcData = 71/100, innerRadius 0.8),
      número "71" headline/large-emphasized dentro + "/100" debajo; a la
      derecha: "Puntaje vocal" (headline/small-emphasized), supporting
      "Afinación estimada sobre la referencia", y 3 chips (Secondary Container):
      "Afinación 71", "Estabilidad 66", "Sin voz 4%".
   b) Divider.
   c) 3 filas métrica con barra manual (track Surface Container High, alto 6,
      radio 3 + fill Primary con ancho = score% del track, medida fija conocida):
      "Afinación 71" / "Estabilidad de pitch 66" / "Control de volumen 80".
5. CARD "Curva de pitch (F0)" (mismo estilo de card):
   a) Header: "Curva de pitch" + leyenda: "● Alumno (Primary)  ● Referencia
      (Outline/terciario)".
   b) Gráfico: frame ~170px alto, fill Surface Container, radio 8, con 2 paths
      SVG (figma.createNodeFromSvg) que simulan la curva F0 alumno y referencia,
      más 3 marcadores verticales Error en los segmentos desafinados.
   c) Nota: "Segmentos en rojo superan 50 cents de desviación" (On Surface
      Variant, 12px).
6. SECCIÓN "Segmentos con mayor desviación" (HU-45/46):
   - Título "Segmentos con mayor desviación" (headline/small).
   - Crear UN componente local "Vocal segment row" con propiedades TEXT
     (Time, Detail, Delta) y añadir 3 instancias:
     · 00:12 — "Nota E4 → F#4 · 45 cents" (delta rojo)
     · 00:27 — "Sin voz detectado (pausa)" — DIFFERENCIAR de desafinación
       (delta en Secondary Container, no rojo)
     · 00:41 — "Nota A4 → G#4 · 72 cents" (delta rojo)
   - Fila: dot indicator (Error / Secondary Container según tipo), textos On
     Surface y On Surface Variant, delta en pill (Error Container + On Error
     Container, o Secondary Container para "sin voz").
7. SECCIÓN "Feedback vocal" (HU-46): componente local "Vocal feedback card"
   (props TEXT: Title, Body), fill Primary Container, radio 12, texto On
   Primary Container. 2 instancias:
   - "Sostén la afinación en el segundo compás" / "Los últimos 3 segundos se
     desviaron hasta 72 cents sobre la referencia."
   - "Ajusta el volumen en la entrada" / "Detectamos 4% del tiempo sin voz;
     esto es distinto a una desafinación."
8. CARD "Evaluación combinada" (HU-47/RF-40): título "Evaluación combinada" +
   "Disponible porque esta rutina incluye baile y canto"; 3 columnas:
   Baile 78 · Canto 71 · COMBINADO 75 (destacado con fill Primary Container /
   On Primary Container); nota "Ponderación: 60% baile / 40% canto"
   (On Surface Variant, 12px).
9. CTA: Button Type=Round, Size=Large, State=Enabled, Show icon=False, label
   "Reproducir comparación", ancho FILL.
10. Navigation Bar: instancia Nav items=4, labels en orden Inicio · Rutinas ·
    Análisis · Perfil; dejar "Análisis" seleccionado si su variant lo permite.
    Último hijo del wrapper (HUG vertical).

ESTADOS — crear como frames hermanos a la derecha del principal:
- "02.1 · Canto — Sin audio" (HU-43): app bar + card centrada con icono SVG
  (micrófono), "Este intento no incluye audio", "No se pudo extraer la curva de
  pitch.", botón tonal "Reintentar".
- "02.2 · Canto — Procesando" (HU-44): "Analizando afinación…", "Paso 2 de 4:
  alineación temporal de pitch", barra de progreso al 45%.

WORKFLOW (aplicar directamente, no requiere skills MCP específicas):
1. PRIMERO crear el wrapper: createAutoLayout('VERTICAL'), nombre "02 · Canto —
   Análisis vocal", resize 412×915, FIXED/FIXED, x = maxX+200 del contenido
   existente, clipsContent, fondo ligado a Surface (o hex fallback #FFFBFE).
2. Después poblar secciones SIEMPRE dentro del wrapper (nunca crearlas top-level
   y reubicarlas). layoutSizingHorizontal='FILL' SOLO después de appendChild.
3. Importar componentes/variables/estilos en paralelo con Promise.all.
4. Colores: setBoundVariableForPaint(...) siempre; si falla, hex fallback (Bloque
   2). Espaciados/radius M3: 8/12/16/24 hardcodeados.
5. Texto: loadFontAsync → mutar → return ids. Overrides en instancias: cargar las
   fuentes del nodo con getStyledTextSegments(['fontName']).
6. Filas/tarjetas repetidas → componente local + addComponentProperty('X','TEXT')
   + componentPropertyReferences y instance.setProperties({...}).
7. Iconos: solo SVG con createNodeFromSvg (width/height explícitos + resize);
   nunca rotar primitivos.
8. placeholder=true durante construcción y quitarlo al terminar cada sección.
9. Devolver SIEMPRE createdNodeIds/mutatedNodeIds estructurados por llamada.

VALIDACIÓN FINAL:
1. get_metadata del wrapper: descendentes deben ser UI editable
   (TEXT/FRAME/INSTANCE/VECTOR), nunca un raster plano del UI.
2. UNA captura de composición completa y comparar con este brief: sin texto
   recortado, sin solapes, sin placeholders sin rellenar ("Label", "Title"),
   tab "Canto" seleccionada, tipografía Roboto.
3. Si hay defecto → fix dirigido + UNA segunda captura (la más reciente es final).
4. Reportar: id del frame principal, ids de los 2 estados, nº de instancias de
   design system vs. nodos manuales, y pendientes.
```

---

## BLOQUE 4 — Fix: completar pantalla "02 · Canto — Análisis vocal"

> Contexto: revisión de `Docs/prototipo.png` contra el BLOQUE 3. Estados 02.1/02.2
> correctos. La pantalla principal quedó incompleta. Ejecuta este fix y revalida.

```
FIX — completar la pantalla principal "02 · Canto — Análisis vocal"
(fileKey: xq0uCROdEaMo3wu4WLFgB7, Page 1)

DEFECTOS DETECTADOS EN LA CAPTURA:
A. Nodos huérfanos FUERA del wrapper: una fila "00:12 · Nota E4 → F#4 · 45 cents"
   y una tarjeta "Sostén la afinación en el segundo compás…" flotan en el canvas,
   debajo de los frames (creados top-level).
B. Faltan dentro del wrapper, ANTES de la Navigation Bar (que debe seguir siendo
   el último hijo):
   1. Nota bajo la curva: "Segmentos en rojo superan 50 cents de desviación"
      (On Surface Variant, 12px) — dentro de la card "Curva de pitch", tras el gráfico.
   2. SECCIÓN "Segmentos con mayor desviación" (título headline/small + 3
      instancias del componente local "Vocal segment row"):
      · 00:12 — "Nota E4 → F#4 · 45 cents" (pill Error Container)
      · 00:27 — "Sin voz detectado (pausa)" (pill Secondary Container, NO rojo)
      · 00:41 — "Nota A4 → G#4 · 72 cents" (pill Error Container)
   3. SECCIÓN "Feedback vocal" (2 instancias de "Vocal feedback card"):
      · "Sostén la afinación en el segundo compás" / "Los últimos 3 segundos se
        desviaron hasta 72 cents sobre la referencia."
      · "Ajusta el volumen en la entrada" / "Detectamos 4% del tiempo sin voz;
        esto es distinto a una desafinación."
   4. CARD "Evaluación combinada" (HU-47/RF-40): título "Evaluación combinada" +
      "Disponible porque esta rutina incluye baile y canto"; columnas Baile 78 ·
      Canto 71 · COMBINADO 75 (destacado Primary Container / On Primary Container);
      nota "Ponderación: 60% baile / 40% canto" (On Surface Variant, 12px).
   5. CTA: Button Type=Round, Size=Large, Show icon=False, label "Reproducir
      comparación", ancho FILL.

PASOS:
1. get_metadata del wrapper y del Page: localizar los 2 nodos huérfanos y las
   secciones 6-9 (¿existen fuera del wrapper, o no existen?).
2. Si las secciones existen top-level → moverlas al wrapper (insertar antes de la
   Navigation Bar). Si NO existen → crearlas siguiendo el workflow del BLOQUE 3
   (poblar SIEMPRE dentro del wrapper; layoutSizingHorizontal='FILL' solo tras
   appendChild). Los componentes MASTERS ("Vocal segment row", "Vocal feedback
   card") pueden vivir top-level; dentro del wrapper deben ir INSTANCIAS.
3. Orden final de hijos del wrapper: App bar · Cabecera · Tabs · Card Puntaje
   vocal · Card Curva de pitch (+nota) · Segmentos (3 filas) · Feedback (2 cards)
   · Evaluación combinada · CTA · Navigation Bar.
4. ALTURA: el wrapper 412×915 FIXED recorta bajo el fold; para validar, pon el
   wrapper a HUG vertical (o alt necesario) y genera la captura final con TODO
   visible; al cerrar, restaura 412 de ancho (decidir con el equipo si queda
   FIXED+scroll o HUG). Regla: nada queda fuera del wrapper ni top-level.
5. Revalidar del BLOQUE 3: sin placeholders, "Canto" seleccionado, Roboto,
   sin solapes; captura final + reportar createdNodeIds/mutatedNodeIds y
   confirmar secciones 6-9 presentes en el árbol del wrapper.
```

---

## BLOQUE 5 — Pulido: iconos de nav + estructura + gráfico

> Entrega: mensaje 1 de 2 (ejecuta los cambios). El BLOQUE 6 va después (valida y reporta).

```
PULIDO — SyncDance "02 · Canto — Análisis vocal"
fileKey: xq0uCROdEaMo3wu4WLFgB7 · Page 1 (id 0:1)

La pantalla principal ya está completa. Ejecuta ESTE pulido (4 puntos):

1) NAV BAR — hoy los 4 items muestran el MISMO icono de estrella.
   Reemplaza cada icono por uno distinto (20-24px, sin tocar los labels):
   · Inicio      → home (casita)
   · Rutinas     → playlist_note (lista con nota) o calendar_month
   · Análisis    → monitoring (barras de analytics) — item SELECCIONADO,
                   icono en On Secondary Container (el label ya está correcto)
   · Perfil      → person
   Método: createNodeFromSvg con paths Material (width/height explícitos +
   resize; nunca rotar primitivos), o swap de icono si la instancia del
   componente lo permite. Si el icono está anidado en la instancia, obtener
   fuentes/estructura con getStyledTextSegments antes de mutar.

2) ESTRUCTURA (auditoría) — get_metadata del Page y confirmar:
   · UN solo wrapper "02 · Canto — Análisis vocal" (ancho 412) cuyo orden de
     hijos sea: App bar → Cabecera → Tabs → Card "Puntaje vocal" → Card
     "Curva de pitch" → sección "Segmentos con mayor desviación" (3
     instancias) → sección "Feedback vocal" (2 instancias) → Card
     "Evaluación combinada" → CTA "Reproducir comparación" → Navigation Bar
     (ÚLTIMO hijo).
   · "02.1 · Canto — Sin audio" y "02.2 · Canto — Procesando" como frames
     hermanos a la derecha del wrapper.
   · CERO nodos sueltos top-level (los MASTERS de "Vocal segment row" y
     "Vocal feedback card" pueden vivir fuera; dentro del wrapper sólo
     INSTANCIAS). Si queda un duplicado huérfano → eliminarlo; si falta
     contenido dentro → moverlo/crear dentro (FILL sólo tras appendChild).

3) GRÁFICO de "Curva de pitch" — el brief pide 3 marcadores verticales
   Error (rojo) en los momentos desafinados: 00:12, 00:27 y 00:41.
   Si sólo hay 2, añadir el que falte (mismo estilo: línea 1-2px, Error).

4) ALTURA — ancho fijo 412; deja la altura en HUG vertical (todo el
   contenido visible, sin clip). NO restaurar 915 a la fuerza: el desvío
   frente al original 412×915 queda reportado como decisión de equipo
   (Figma no puede saber si la app lleva scroll fijo).

Devuelve: createdNodeIds/mutatedNodeIds estructurados por llamada + resumen
de get_metadata del wrapper (nº de hijos por sección).
```

---

## BLOQUE 6 — Validación final + reporte de entrega

> Entrega: mensaje 2 de 2 (tras el BLOQUE 5). No pide cambios salvo defectos.

```
VALIDACIÓN FINAL — SyncDance "02 · Canto — Análisis vocal"
fileKey: xq0uCROdEaMo3wu4WLFgB7 · Page 1 (id 0:1)

1) ESTRUCTURA: get_metadata del wrapper → todos los descendientes deben ser
   UI editable (TEXT/FRAME/INSTANCE/VECTOR), nunca un raster plano del UI y
   nunca nodos fuera del wrapper.

2) UNA captura de las 3 pantallas juntas y verificar contra este checklist:
   · Sin placeholders sin rellenar ("Label", "Title", "Subtitle")
   · Sin texto recortado ni solapes; tipografía Roboto en todo
   · Tab "Canto" seleccionada (subrayado Primary), "Danza" inactiva
   · Puntaje vocal: anillo 71/100 · chips 71/66/4% · barras 71/66/80
   · Curva: leyenda Alumno/Referencia · nota "50 cents" · 3 marcadores rojos
   · Segmentos: 00:12 (45 cents rojo) · 00:27 (Sin voz morado) · 00:41 (72 cents rojo)
   · Feedback: 2 cards "Sostén la afinación…" y "Ajusta el volumen…"
   · Evaluación combinada: 78 · 71 · 75 destacado · "60% baile / 40% canto"
   · CTA "Reproducir comparación" + nav con iconos DIFERENTES y "Análisis" activo
   · Estados 02.1 (micrófono + Reintentar) y 02.2 (paso 2 de 4 · 45%)

3) Si aparece CUALQUIER defecto → fix dirigido + UNA segunda captura
   (la captura más reciente es la final).

4) REPORTE DE ENTREGA:
   · id del frame principal + ids de los 2 estados
   · nº de instancias de design system vs. nodos manuales
   · propiedades TEXT expuestas en "Vocal segment row" y "Vocal feedback card"
   · desvíos abiertos: altura HUG vs 412×915 (decisión de equipo),
     disclaimer "Curva conceptual ilustrativa" añadido (confirmar si se queda)
   · pendientes, si los hay
```
