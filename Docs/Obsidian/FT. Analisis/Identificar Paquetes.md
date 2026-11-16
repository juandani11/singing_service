### P1. Módulo de Usuarios y Autenticación

Este paquete abarca las funcionalidades que permiten a alumnos e instructores registrarse en la plataforma, autenticarse de manera segura y gestionar su perfil personal (nombre, avatar y datos básicos). Además, incluye la validación estricta de permisos por roles (alumno/instructor) mediante tokens seguros (JWT) y el mecanismo para que los instructores vinculen a sus alumnos a través de códigos de invitación. Garantiza el control de acceso inicial y la protección de la información, asegurando que solo usuarios validados accedan a las rutas y recursos protegidos del sistema.

### P2. Módulo de Gestión de Rutinas

Este paquete engloba las herramientas destinadas a los instructores para administrar el contenido pedagógico: crear, listar, editar y eliminar rutinas maestras, así como cargar, validar y reproducir videos de referencia con instrucciones y niveles de dificultad. Incluye la capacidad de asignar estas rutinas a uno o varios alumnos. Para los alumnos, este paquete provee el acceso al catálogo de rutinas asignadas y la visualización del detalle técnico y el video maestro, facilitando la distribución ordenada y centralizada del material de práctica de baile y canto.

### P3. Módulo de Grabación y Carga de Intentos

Este paquete se encarga de gestionar la captura y transferencia de las prácticas de los alumnos. Permite grabar video y audio desde la app móvil, subir estos archivos con indicadores de progreso y validaciones de formato, y reintentar cargas fallidas sin generar registros duplicados. A nivel de sistema, se encarga de enviar el intento a una cola de procesamiento asíncrono, actualizar el estado del intento (pendiente, procesando, completado, fallido) y optimizar los tiempos de respuesta mediante el preprocesamiento y almacenamiento en caché de las características de los videos maestros para su futura reutilización.

### P4. Módulo de Análisis Biomecánico

Este paquete contiene el motor algorítmico central para la evaluación del movimiento. Se encarga de extraer los puntos anatómicos (landmarks/pose) frame a frame de los videos del alumno y del maestro, normalizar las coordenadas (escala y orientación) y alinear temporalmente ambas secuencias. A partir de esto, calcula ángulos, trayectorias y diferencias exactas por articulación, detecta desviaciones mediante umbrales configurables, registra microerrores con marcas de tiempo y genera un puntaje parcial por segmento corporal (brazos, torso, cadera y piernas) que se consolida en un puntaje global de 0 a 100. Finalmente, garantiza la persistencia de métricas y la trazabilidad de todo el análisis.

### P5. Módulo de Análisis de Audio y Canto

Este paquete se especializa en el procesamiento de la voz y la evaluación musical. Extrae la curva de frecuencia fundamental (pitch/F0) tanto del audio del alumno como de la referencia, y evalúa la afinación comparando ambas pistas para generar un puntaje vocal y detectar errores de entonación. Además, se encarga de generar un feedback vocal identificando los segmentos desafinados con recomendaciones específicas, y realiza el cálculo de la evaluación compuesta multimodal, que fusiona los resultados del análisis biomecánico (baile) y del análisis de audio (canto) para determinar el rendimiento integral del alumno.

### P6. Módulo de Retroalimentación y Visualización

Este paquete agrupa las funcionalidades de interacción visual y pedagógica para el alumno. Se encarga de generar un feedback técnico claro con recomendaciones concretas basadas en los resultados de la IA y de exponer en pantalla el puntaje global, los puntajes parciales y el listado de errores principales. Proporciona una experiencia de reproducción comparativa sincronizada lado a lado (maestro vs. alumno), permitiendo activar un overlay (superposición) del esqueleto de pose para identificar visualmente las diferencias posturales y facilitando la navegación mediante marcadores temporales para saltar directamente a los momentos exactos donde ocurrieron los microerrores.

### P7. Módulo de Seguimiento y Progreso

Este paquete proporciona las herramientas de monitoreo y analítica a largo plazo para ambos roles. Para el alumno, ofrece el historial cronológico de sus intentos por rutina y fecha, así como gráficos de evolución que muestran su mejora en la puntuación a lo largo del tiempo, además de notificaciones cuando sus análisis han finalizado. Para el instructor, incluye un dashboard (panel de control) global con el estado de sus alumnos y resultados, la capacidad de auditar el detalle técnico de cualquier intento y la funcionalidad para exportar informes técnicos en formato PDF, facilitando una visión macro y micro del progreso pedagógico de la clase.