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
