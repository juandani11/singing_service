# 1. Identificar Actores y Casos de Uso 
## Actores 

| Actor                                                       | Descripción                                                                                                                                                                                                                                                                                                                            |
| ----------------------------------------------------------- | -------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| **Alumno**                                                  | Usuario final que consulta rutinas asignadas o disponibles, graba y sube intentos, consulta resultados, feedback, historial y evolución de su progreso.                                                                                                                                                                                |
| **Instructor**                                              | Usuario que administra rutinas maestras, carga videos de referencia, asigna rutinas, vincula alumnos y supervisa intentos y resultados mediante un dashboard.                                                                                                                                                                          |
| **Sistema de Procesamiento Asíncrono / Worker de análisis** | Actor secundario técnico opcional. Representa el proceso que consume la cola asíncrona, ejecuta el análisis biomecánico y de audio, actualiza estados y dispara notificaciones. Si se modela como componente interno del sistema, no debe considerarse actor externo; sus casos de uso quedarían como procesos internos automatizados. |
## Casos de Uso 

## 2. Casos de Uso

### 2.1 Módulo de Usuarios y Autenticación

| ID    | Caso de Uso                                               | Actor(es)           | RF    |
| ----- | --------------------------------------------------------- | ------------------- | ----- |
| CU-01 | Registrar cuenta de alumno o instructor                   | Alumno / Instructor | RF-01 |
| CU-02 | Iniciar sesión                                            | Alumno / Instructor | RF-02 |
| CU-03 | Validar permisos de rol en acceso a recurso protegido     | Sistema / Worker    | RF-03 |
| CU-04 | Consultar perfil básico                                   | Alumno / Instructor | RF-04 |
| CU-05 | Actualizar perfil básico (nombre, avatar y datos básicos) | Alumno / Instructor | RF-04 |
| CU-06 | Vincular alumno mediante código o invitación              | Instructor          | RF-05 |

### 2.2 Módulo de Gestión de Rutinas

| ID    | Caso de Uso                                                                 | Actor(es)  | RF    |
| ----- | --------------------------------------------------------------------------- | ---------- | ----- |
| CU-07 | Crear rutina maestra                                                        | Instructor | RF-06 |
| CU-08 | Listar rutinas maestras                                                     | Instructor | RF-06 |
| CU-09 | Ver detalle de rutina maestra                                               | Instructor | RF-06 |
| CU-10 | Editar rutina maestra                                                       | Instructor | RF-06 |
| CU-11 | Eliminar rutina maestra                                                     | Instructor | RF-06 |
| CU-12 | Cargar y validar video de referencia de rutina                              | Instructor | RF-07 |
| CU-13 | Reproducir video de referencia de rutina                                    | Instructor | RF-07 |
| CU-14 | Asignar rutina a uno o varios alumnos                                       | Instructor | RF-08 |
| CU-15 | Consultar rutinas asignadas o catálogo disponible                           | Alumno     | RF-09 |
| CU-16 | Ver detalle de rutina (instrucciones, dificultad, duración y video maestro) | Alumno     | RF-10 |

### 2.3 Módulo de Grabación y Carga de Intentos

| ID    | Caso de Uso                                                                | Actor(es)        | RF    |
| ----- | -------------------------------------------------------------------------- | ---------------- | ----- |
| CU-17 | Grabar video y audio desde app móvil                                       | Alumno           | RF-11 |
| CU-18 | Subir archivo de intento con indicador de progreso y validaciones          | Alumno           | RF-12 |
| CU-19 | Consultar estado del intento                                               | Alumno           | RF-13 |
| CU-20 | Reintentar carga fallida sin duplicar intento                              | Alumno           | RF-14 |
| CU-21 | Enviar análisis de intento a cola asíncrona                                | Sistema / Worker | RF-15 |
| CU-22 | Actualizar estado del intento (pendiente, procesando, completado, fallido) | Sistema / Worker | RF-13 |
| CU-23 | Preprocesar video maestro y reutilizar características                     | Sistema / Worker | RF-16 |

### 2.4 Módulo de Análisis Biomecánico

| ID    | Caso de Uso                                                            | Actor(es)        | RF    |
| ----- | ---------------------------------------------------------------------- | ---------------- | ----- |
| CU-24 | Extraer landmarks/pose por frame de alumno y maestro                   | Sistema / Worker | RF-17 |
| CU-25 | Normalizar coordenadas, escala y orientación                           | Sistema / Worker | RF-18 |
| CU-26 | Alinear temporalmente alumno y maestro                                 | Sistema / Worker | RF-19 |
| CU-27 | Calcular ángulos, trayectorias y diferencias por articulación/segmento | Sistema / Worker | RF-20 |
| CU-28 | Detectar desviaciones sobre umbrales configurables                     | Sistema / Worker | RF-21 |
| CU-29 | Registrar microerrores con timestamp                                   | Sistema / Worker | RF-22 |
| CU-30 | Calcular puntaje por segmento (brazos, torso, cadera y piernas)        | Sistema / Worker | RF-23 |
| CU-31 | Calcular puntaje global ponderado de 0 a 100                           | Sistema / Worker | RF-24 |
| CU-32 | Persistir métricas, errores, mensajes y trazabilidad                   | Sistema / Worker | RF-25 |

### 2.5 Módulo de Análisis de Audio y Canto

| ID    | Caso de Uso                                                        | Actor(es)        | RF    |
| ----- | ------------------------------------------------------------------ | ---------------- | ----- |
| CU-33 | Extraer curva de pitch (F0) de alumno y referencia                 | Sistema / Worker | RF-26 |
| CU-34 | Evaluar afinación y generar puntaje/errores vocales                | Sistema / Worker | RF-27 |
| CU-35 | Generar feedback vocal con segmentos desafinados y recomendaciones | Sistema / Worker | RF-28 |
| CU-36 | Calcular evaluación compuesta multimodal de baile y canto          | Sistema / Worker | RF-29 |

### 2.6 Módulo de Retroalimentación y Visualización

| ID    | Caso de Uso                                                         | Actor(es)        | RF    |
| ----- | ------------------------------------------------------------------- | ---------------- | ----- |
| CU-37 | Generar feedback técnico con recomendaciones concretas              | Sistema / Worker | RF-30 |
| CU-38 | Visualizar puntaje global, puntajes parciales y errores principales | Alumno           | RF-31 |
| CU-39 | Reproducir comparación sincronizada maestro/alumno                  | Alumno           | RF-32 |
| CU-40 | Visualizar overlay de pose en la comparación                        | Alumno           | RF-33 |
| CU-41 | Saltar a microerrores mediante marcadores temporales                | Alumno           | RF-34 |

### 2.7 Módulo de Seguimiento y Progreso

| ID    | Caso de Uso                                                       | Actor(es)                 | RF    |
| ----- | ----------------------------------------------------------------- | ------------------------- | ----- |
| CU-42 | Consultar historial de intentos por rutina y fecha                | Alumno                    | RF-35 |
| CU-43 | Visualizar evolución de puntuación y métricas                     | Alumno                    | RF-36 |
| CU-44 | Visualizar dashboard de alumnos, intentos, estados y resultados   | Instructor                | RF-37 |
| CU-45 | Revisar detalle de intento (métricas, errores y evidencia visual) | Instructor                | RF-38 |
| CU-46 | Generar informe técnico del intento                               | Instructor                | RF-39 |
| CU-47 | Notificar finalización del procesamiento al alumno                | Sistema / Worker / Alumno | RF-40 |

### Relaciones include/extend propuestas

| Relación      | Tipo    | Justificación                                                                           |
| ------------- | ------- | --------------------------------------------------------------------------------------- |
| CU-05 → CU-04 | extend  | Actualizar perfil se realiza opcionalmente desde consultar perfil.                      |
| CU-12 → CU-07 | extend  | Cargar video de referencia es opcional al crear rutina.                                 |
| CU-12 → CU-10 | extend  | Cargar video de referencia es opcional al editar rutina.                                |
| CU-13 → CU-09 | extend  | Reproducir video es opcional desde el detalle de rutina del instructor.                 |
| CU-13 → CU-16 | extend  | Reproducir video es opcional desde el detalle de rutina del alumno.                     |
| CU-16 → CU-15 | extend  | Ver detalle se realiza opcionalmente desde el catálogo/rutinas asignadas.               |
| CU-18 → CU-21 | include | Subir un intento dispara el envío a la cola asíncrona de análisis.                      |
| CU-20 → CU-18 | extend  | Reintentar carga solo aplica cuando una carga falló.                                    |
| CU-24 → CU-25 | include | Extraer landmarks requiere normalizar coordenadas, escala y orientación.                |
| CU-27 → CU-26 | include | Calcular diferencias requiere alineación temporal alumno-maestro.                       |
| CU-28 → CU-27 | include | Detectar desviaciones usa ángulos, trayectorias y diferencias calculadas.               |
| CU-29 → CU-28 | include | Registrar microerrores requiere detectar desviaciones.                                  |
| CU-31 → CU-30 | include | El puntaje global requiere los puntajes por segmento.                                   |
| CU-34 → CU-33 | include | Evaluar afinación requiere extraer la curva de pitch F0.                                |
| CU-35 → CU-34 | include | Generar feedback vocal requiere la evaluación de afinación.                             |
| CU-36 → CU-31 | include | La evaluación compuesta requiere el puntaje de baile.                                   |
| CU-36 → CU-35 | include | La evaluación compuesta requiere el feedback/evaluación vocal.                          |
| CU-37 → CU-32 | include | El feedback técnico usa métricas, errores y trazabilidad persistidos.                   |
| CU-40 → CU-39 | extend  | Mostrar overlay de pose es opcional durante la comparación sincronizada.                |
| CU-41 → CU-39 | extend  | Saltar a microerrores es opcional durante la reproducción comparada.                    |
| CU-43 → CU-42 | include | Visualizar evolución requiere consultar el historial.                                   |
| CU-45 → CU-44 | extend  | Revisar detalle de intento se realiza opcionalmente desde el dashboard.                 |
| CU-46 → CU-45 | include | Generar informe técnico requiere revisar el detalle del intento.                        |
| CU-47 → CU-22 | extend  | Notificar finalización ocurre cuando el estado del intento cambia a completado/fallido. |
## 3 Priorizar Caso de Uso

- **Crítico**: sin esto el flujo principal del producto no funciona (autenticación, rutinas, carga de intentos, pipeline de análisis, feedback y comparación).
- **Alto**: necesario para una experiencia completa, pero no bloquea el núcleo.
- **Medio**: mejora la usabilidad o es complementario.
- **Bajo**: no se identificaron casos de uso con prioridad baja en este alcance; todos aportan valor.

| Código | Caso de uso                                                                 | Actor principal           | Prioridad |
| ------ | --------------------------------------------------------------------------- | ------------------------- | --------- |
| CU-01  | Registrar cuenta de alumno o instructor                                     | Alumno / Instructor       | Crítico   |
| CU-02  | Iniciar sesión                                                              | Alumno / Instructor       | Crítico   |
| CU-03  | Validar permisos de rol en acceso a recurso protegido                       | Sistema / Worker          | Crítico   |
| CU-04  | Consultar perfil básico                                                     | Alumno / Instructor       | Medio     |
| CU-05  | Actualizar perfil básico (nombre, avatar y datos básicos)                   | Alumno / Instructor       | Medio     |
| CU-06  | Vincular alumno mediante código o invitación                                | Instructor                | Alto      |
| CU-07  | Crear rutina maestra                                                        | Instructor                | Crítico   |
| CU-08  | Listar rutinas maestras                                                     | Instructor                | Alto      |
| CU-09  | Ver detalle de rutina maestra                                               | Instructor                | Alto      |
| CU-10  | Editar rutina maestra                                                       | Instructor                | Crítico   |
| CU-11  | Eliminar rutina maestra                                                     | Instructor                | Alto      |
| CU-12  | Cargar y validar video de referencia de rutina                              | Instructor                | Crítico   |
| CU-13  | Reproducir video de referencia de rutina                                    | Instructor                | Alto      |
| CU-14  | Asignar rutina a uno o varios alumnos                                       | Instructor                | Crítico   |
| CU-15  | Consultar rutinas asignadas o catálogo disponible                           | Alumno                    | Crítico   |
| CU-16  | Ver detalle de rutina (instrucciones, dificultad, duración y video maestro) | Alumno                    | Alto      |
| CU-17  | Grabar video y audio desde app móvil                                        | Alumno                    | Crítico   |
| CU-18  | Subir archivo de intento con indicador de progreso y validaciones           | Alumno                    | Crítico   |
| CU-19  | Consultar estado del intento                                                | Alumno                    | Alto      |
| CU-20  | Reintentar carga fallida sin duplicar intento                               | Alumno                    | Medio     |
| CU-21  | Enviar análisis de intento a cola asíncrona                                 | Sistema / Worker          | Crítico   |
| CU-22  | Actualizar estado del intento (pendiente, procesando, completado, fallido)  | Sistema / Worker          | Crítico   |
| CU-23  | Preprocesar video maestro y reutilizar características                      | Sistema / Worker          | Alto      |
| CU-24  | Extraer landmarks/pose por frame de alumno y maestro                        | Sistema / Worker          | Crítico   |
| CU-25  | Normalizar coordenadas, escala y orientación                                | Sistema / Worker          | Crítico   |
| CU-26  | Alinear temporalmente alumno y maestro                                      | Sistema / Worker          | Crítico   |
| CU-27  | Calcular ángulos, trayectorias y diferencias por articulación/segmento      | Sistema / Worker          | Crítico   |
| CU-28  | Detectar desviaciones sobre umbrales configurables                          | Sistema / Worker          | Crítico   |
| CU-29  | Registrar microerrores con timestamp                                        | Sistema / Worker          | Alto      |
| CU-30  | Calcular puntaje por segmento (brazos, torso, cadera y piernas)             | Sistema / Worker          | Crítico   |
| CU-31  | Calcular puntaje global ponderado de 0 a 100                                | Sistema / Worker          | Crítico   |
| CU-32  | Persistir métricas, errores, mensajes y trazabilidad                        | Sistema / Worker          | Crítico   |
| CU-33  | Extraer curva de pitch (F0) de alumno y referencia                          | Sistema / Worker          | Crítico   |
| CU-34  | Evaluar afinación y generar puntaje/errores vocales                         | Sistema / Worker          | Crítico   |
| CU-35  | Generar feedback vocal con segmentos desafinados y recomendaciones          | Sistema / Worker          | Alto      |
| CU-36  | Calcular evaluación compuesta multimodal de baile y canto                   | Sistema / Worker          | Crítico   |
| CU-37  | Generar feedback técnico con recomendaciones concretas                      | Sistema / Worker          | Crítico   |
| CU-38  | Visualizar puntaje global, puntajes parciales y errores principales         | Alumno                    | Crítico   |
| CU-39  | Reproducir comparación sincronizada maestro/alumno                          | Alumno                    | Crítico   |
| CU-40  | Visualizar overlay de pose en la comparación                                | Alumno                    | Alto      |
| CU-41  | Saltar a microerrores mediante marcadores temporales                        | Alumno                    | Alto      |
| CU-42  | Consultar historial de intentos por rutina y fecha                          | Alumno                    | Alto      |
| CU-43  | Visualizar evolución de puntuación y métricas                               | Alumno                    | Alto      |
| CU-44  | Visualizar dashboard de alumnos, intentos, estados y resultados             | Instructor                | Alto      |
| CU-45  | Revisar detalle de intento (métricas, errores y evidencia visual)           | Instructor                | Alto      |
| CU-46  | Generar informe técnico del intento                                         | Instructor                | Medio     |
| CU-47  | Notificar finalización del procesamiento al alumno                          | Sistema / Worker / Alumno | Medio     |
### Observaciones rápidas

- Los **CU críticos** concentran el MVP: registro/login, gestión de rutinas, asignación, carga de intentos, pipeline biomecánico/audio, feedback y visualización comparada.
- Los **CU de prioridad media** pueden posponerse a una segunda iteración sin romper el flujo principal.
- Si tu cliente exige el **análisis de canto desde la primera versión**, CU-33, CU-34 y CU-36 ya están marcados como críticos; si no, podrían bajar a “Alto”.
- CU-23 y CU-29 son optimizaciones: importantes para rendimiento y detalle, pero pueden implementarse después del pipeline básico.