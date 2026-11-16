#### CU-15: Consultar rutinas asignadas

| Campo                 | Detalle                                                                                                                                                                                                   |
| --------------------- | --------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| **Caso de Uso**       | CU-15: Consultar rutinas asignadas                                                                                                                                                                        |
| **Propósito**         | Permitir al alumno ver las rutinas que debe practicar.                                                                                                                                                    |
| **Descripción**       | El alumno accede a su panel y visualiza las rutinas asignadas por sus instructores.                                                                                                                       |
| **Actores**           | Alumno                                                                                                                                                                                                    |
| **Actores Iniciador** | Alumno                                                                                                                                                                                                    |
| **Precondición**      | Sesión activa de alumno.                                                                                                                                                                                  |
| **Flujo de Suceso**   | **Consultar rutinas**  <br>1. El alumno accede al módulo "Mis Rutinas".  <br>2. El sistema busca las asignaciones activas.  <br>3. Se muestra el listado con el nombre, instructor y fecha de asignación. |
| **Postcondición**     | El alumno visualiza sus rutinas asignadas.                                                                                                                                                                |
| **Excepción**         | **Sin rutinas**  <br>1. El alumno no tiene rutinas asignadas.  <br>2. Se muestra un mensaje informativo indicando que debe esperar asignaciones.                                                          |
