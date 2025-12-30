# Code Review Rules – Proyecto Calidad Agente Multibanco B&L

Estas reglas definen los criterios de calidad que deben cumplirse en el código del proyecto.

## 1. Seguridad

- No se permiten tokens, claves API o secretos escritos directamente en el código.
- Todas las credenciales deben manejarse mediante variables de entorno.
- No exponer información sensible en logs o respuestas HTTP.

## 2. Manejo de errores

- Todos los endpoints deben manejar errores correctamente.
- Usar códigos HTTP adecuados (400, 401, 404, 500).
- No devolver trazas internas al cliente.

## 3. Calidad del código

- El código debe ser claro, legible y fácil de mantener.
- Usar nombres descriptivos para funciones, variables y módulos.
- Evitar lógica innecesaria o duplicada.

## 4. Pruebas

- Cada endpoint debe tener al menos una prueba asociada.
- Las pruebas deben validar respuestas correctas y errores esperados.
- Mantener una cobertura de pruebas razonable.

## 5. Mantenibilidad

- Evitar código muerto o imports no utilizados.
- Mantener una estructura ordenada del proyecto.
- Seguir buenas prácticas del framework Flask.
