# Requisitos Funcionales por Módulo

## Módulo de Usuarios y Autenticación

| Código | Requisito                                                                                             |
| ------ | ----------------------------------------------------------------------------------------------------- |
| RF-01  | El alumno e instructor pueden registrarse con datos básicos.                                          |
| RF-02  | El sistema permite iniciar sesión de forma segura y emitir credenciales/tokens para acceso protegido. |
| RF-03  | El sistema restringe acciones y recursos según el rol del usuario.                                    |
| RF-04  | El usuario puede consultar y editar su perfil básico (nombre, avatar opcional y datos básicos).       |
| RF-05  | El instructor puede vincularse con alumnos mediante código o invitación simple.                       |

## Módulo de Gestión de Rutinas

| Código | Requisito                                                                                         |
| ------ | ------------------------------------------------------------------------------------------------- |
| RF-06  | El instructor puede crear, listar, ver, editar y eliminar rutinas maestras.                       |
| RF-07  | El instructor puede cargar, validar y reproducir el video de referencia de una rutina.            |
| RF-08  | El instructor puede asignar rutinas a uno o varios alumnos.                                       |
| RF-09  | El alumno puede listar rutinas asignadas o disponibles en su catálogo.                            |
| RF-10  | El sistema muestra el detalle de la rutina (instrucciones, dificultad, duración y video maestro). |

## Módulo de Grabación y Carga de Intentos

| Código | Requisito |
|---|---|
| RF-11 | El alumno puede grabar video y audio desde la app móvil. |
| RF-12 | El sistema permite subir archivos con indicador de progreso y validaciones. |
| RF-13 | El sistema gestiona el estado del intento (pendiente, procesando, completado y fallido). |
| RF-14 | El alumno puede reintentar una carga fallida sin duplicar el intento. |
| RF-15 | El sistema envía el análisis a workers en cola asíncrona, desacoplándolo de la solicitud web. |
| RF-16 | El sistema preprocesa el video maestro extrayendo y reutilizando características cuando sea posible. |

## Módulo de Análisis Biomecánico (Visión por Computadora)

| Código | Requisito |
|---|---|
| RF-17 | El sistema extrae landmarks/pose por frame del alumno y maestro. |
| RF-18 | El sistema normaliza coordenadas, escala y orientación para una comparación robusta. |
| RF-19 | El sistema alinea temporalmente al alumno y maestro compensando desfases de inicio y velocidad. |
| RF-20 | El sistema calcula ángulos, trayectorias y diferencias por articulación/segmento. |
| RF-21 | El sistema detecta desviaciones que superan umbrales configurables. |
| RF-22 | El sistema registra microerrores con timestamp en los momentos de mayores desviaciones. |
| RF-23 | El sistema calcula el puntaje por segmento (brazos, torso, cadera y piernas). |
| RF-24 | El sistema calcula un puntaje global de 0 a 100 con ponderación definida. |
| RF-25 | El sistema persiste métricas, errores, mensajes y trazabilidad del procesamiento. |

## Módulo de Análisis de Audio y Canto

| Código | Requisito |
|---|---|
| RF-26 | El sistema extrae la curva de pitch (F0) del audio del alumno y la referencia. |
| RF-27 | El sistema evalúa la afinación comparando pitch y produce puntaje/errores vocales. |
| RF-28 | El sistema genera feedback vocal mostrando segmentos desafinados y recomendaciones básicas. |
| RF-29 | El sistema combina baile y canto en una evaluación compuesta (puntaje multimodal) cuando aplique. |

## Módulo de Retroalimentación y Visualización

| Código | Requisito |
|---|---|
| RF-30 | El sistema genera feedback técnico con recomendaciones concretas basadas en errores detectados. |
| RF-31 | El alumno visualiza su puntaje global, puntajes parciales y principales errores. |
| RF-32 | El sistema provee un reproductor sincronizado de maestro y alumno con controles temporales coordinados. |
| RF-33 | El sistema superpone esqueletos o puntos articulares (overlay de pose) para facilitar la comparación. |
| RF-34 | El sistema permite saltar a los instantes con microerrores detectados mediante marcadores. |

## Módulo de Seguimiento y Progreso

| Código | Requisito                                                                                              |
| ------ | ------------------------------------------------------------------------------------------------------ |
| RF-35  | El alumno puede consultar su historial de intentos anteriores por rutina y fecha.                      |
| RF-36  | El sistema muestra la evolución del alumno (tendencia de puntuación y métricas a lo largo del tiempo). |
| RF-37  | El instructor visualiza un dashboard con el listado de alumnos, intentos, estados y resultados.        |
| RF-38  | El instructor puede revisar el detalle de un intento (métricas, errores y evidencia visual).           |
| RF-39  | El sistema genera una vista de informe técnico del intento (exportación PDF queda como mejora).        |
| RF-40  | El sistema notifica al alumno cuando el procesamiento del intento finaliza.                            |
