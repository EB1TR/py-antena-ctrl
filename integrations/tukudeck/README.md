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
