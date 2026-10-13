# TukuDeck

Plugin de Stream Deck para controlar y visualizar las estaciones, antenas,
rotores y telemetría de py-antena-ctrl mediante MQTT.

## Versión 1.2.1

- La primera lectura de telemetría tras `--` aparece inmediatamente, incluso
  con un promedio configurado; las siguientes lecturas respetan el promedio.
- La frecuencia `0` sigue indicando que no hay slice y muestra `--`, sin
  afectar a los demás datos recibidos por sus propios topics MQTT.
- Una banda de radio recibida como `[0, 0]` muestra `N/A`; `--` queda reservado
  para la ausencia o caducidad de ese dato.

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

La telemetría de cada estación se muestra a partir de su propio topic MQTT
(`stn1/...` o `stn2/...`), sin depender de que exista un slice ni del estado
`available`. Cada dato muestra `--` si no se ha recibido una lectura válida o
si su topic lleva 5 segundos sin actualizarse; los demás datos no se ocultan.
El cero es una lectura válida salvo en la frecuencia: `qrg = 0` indica que no
hay slice y muestra `--` solo en ese dato. Una banda recibida `[0, 0]` muestra
`N/A`. La primera lectura tras `--` aparece inmediatamente,
sin esperar a completar el número de muestras del promedio configurado.

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
