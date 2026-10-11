# TukuDeck

Plugin de Stream Deck para controlar y visualizar las estaciones, antenas,
rotores y telemetría de py-antena-ctrl mediante MQTT.

## Desarrollo

Requiere Node.js 24 o posterior.

```bash
npm ci
npm run build
```

El bundle generado se escribe en
`com.eb1tr.tukudeck.sdPlugin/bin/plugin.js`. El plugin se ejecuta en el equipo
que tenga instalada la aplicación Stream Deck; no forma parte de Docker
Compose.

La conexión MQTT se configura actualmente en `src/mqtt.ts`.

## Acciones

El plugin incluye únicamente las acciones configurables actuales. Se han eliminado
las acciones antiguas individuales de antena, banda y rotor, PARK y las pruebas.
Los UUID de las acciones configurables se conservan. Si un perfil todavía usa
una acción antigua eliminada, sustituye esa tecla por la acción configurable
correspondiente y selecciona su antena, banda o rotor. Para PARK puedes usar
Rotor - Preset con la dirección deseada.

Las acciones **Stack - Antena** y **Stack - Swap** permiten elegir STN1 o
STN2. Ambas actúan sobre el stack de la banda activa de la estación elegida;
las teclas de antena muestran el estado correspondiente a esa misma estación.

TW1, TW2 y TW3 tienen un color global configurable. El color de cada rotor se
aplica automáticamente a sus teclas de posición, paso y preset.

Si un rotor deja de publicar su posición durante 10 segundos, su tecla de
posición muestra `--°` y alterna cada segundo entre rojo y el color configurado
hasta que vuelve a recibirse una posición válida.

### Meteo - Datos

Nueva tecla que recibe las mediciones retenidas de `meteo/tuku` (proyecto
`meteo-tuku`). Permite seleccionar y ordenar temperatura exterior, humedad,
velocidad y dirección del viento, racha actual y máxima diaria, ritmo de
lluvia y acumulado de hoy. Cada tecla tiene selección, intervalo y color propios.

El intervalo es configurable entre 1 y 60 segundos (por defecto, 5). Pulsar
avanza al siguiente dato y reinicia el intervalo; seleccionar solo un dato
lo mantiene fijo. Desmarcar todos muestra `SIN SELECCIÓN`.

Los datos ausentes o con más de cinco minutos de antigüedad muestran `--`
en gris. Se comprueba la fecha del paquete retenido, no solo la hora de
recepción MQTT. Las teclas ocultas liberan sus temporizadores y suscripciones.
El botón es informativo: no envía órdenes ni cambia antenas o rotores.

Pruebas automatizadas de la meteorología y el guardado de los selectores:

```bash
node --test tests/weather.test.mjs
```
