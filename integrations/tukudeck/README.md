# TukuDeck

Plugin de Stream Deck para controlar y visualizar las estaciones, antenas,
rotores y telemetría de py-antena-ctrl mediante MQTT.

## Versión actual: 1.8.0

RX A/B funcionan como pulsaciones breves en Maestro: abren o cierran receptores, ambos pueden estar verdes incluso muteados. Con dos panadapters del mismo cliente recorren primero → segundo → cerrado (se recrea el slice conservando frecuencia, modo, filtros, audio y asignaciones). Los panadapters siguen el orden de recepción del cliente. A se debe abrir antes que B cuando no existe ningún slice. RX A puede abrir el primero usando el centro del panadapter y la persistencia de modo del FLEX. TX A/B asignan TX sin emitir. TX B con B cerrado crea un split de 1 kHz en CW/RTTY/DIGL/DIGU o 5 kHz en otros modos, conservando el foco en A. Se rechazan operaciones ambiguas entre clientes y cambios durante TX. Las secuencias se ejecutan con confirmación paso a paso.

La tecla SPLIT especial conserva su lógica y todas sus opciones de audio, desplazamiento y cierre de B. Requiere actualizar los puentes FLEX. Esta versión implementa las pulsaciones breves RX/TX; no añade RIT/XIT por pulsación larga.

## Versión 1.5.1

- El botón SPLIT permite configurar **Silenciar B: Sí / No** (por defecto No).
- Al activar SPLIT se aplica la preferencia al slice B creado o reutilizado,
  sin modificar el mute de A. Desactivar SPLIT solo devuelve TX al receptor;
  no cambia de nuevo el audio de B.
- Requiere actualizar también los puentes FLEX de STN1/STN2.

## Versión 1.5.0

- El mensaje `stnN/band` contiene solo un entero, por ejemplo `20`, sin segmento.
- El estado de radio elimina el campo segmento. Se mantiene lectura del formato
  anterior durante la actualización de los puentes, tomando únicamente la banda.
- `0` representa N/A y un dato que caduca muestra `--`.

## Versión 1.4.1

- TUNE, MOX y ATU usan el mismo selector STN1/STN2 que el resto de teclas.
- SPLIT crea B explícitamente en el panadapter/waterfall del receptor original.
  Solo reutiliza un segundo slice si pertenece al mismo cliente y waterfall.
- El desplazamiento de SPLIT continúa siendo configurable por tecla.

## Versión 1.4.0

- **TRX - SPLIT**: pulsar activa el split y otra pulsación devuelve TX al receptor.
- Selector STN1/STN2 y desplazamiento configurable en kHz, con signo y por
  defecto +1 kHz. Crea B si no existe; si ya existe, lo sintoniza al desplazamiento.
  Al desactivar conserva B.
- Los paneles MOX, TUNE y ATU muestran el selector de estación con controles
  locales, sin depender de la descarga de componentes de Internet.
- Requiere reconstruir los servicios `flex-stn1` y `flex-stn2` del servidor.

## Versión 1.3.1

- El puente renueva TX/RX mientras recibe respuestas TCP del FLEX, aunque no
  cambie interlock. Los botones mantienen el estado en reposo sin caducar.
- Al reconectar con la radio se espera un estado interlock nuevo antes de
  renovar el heartbeat; no se reutiliza el TX de la sesión anterior.

## Versión 1.3.0

- **TRX - MOX**: una pulsación activa TX; la siguiente lo desactiva.
- **TRX - TUNE**: una pulsación activa la portadora; la siguiente la apaga.
- **TRX - ATU**: una pulsación inicia el ajuste automático; la siguiente pone
  el acoplador en bypass. El ciclo termina solo; el ATU puede quedar activo.
- Cada botón permite elegir STN1 o STN2. Se bloquean pulsaciones repetidas
  mientras se espera confirmación, se muestran los errores de FLEX y «Sin datos»
  cuando falta el heartbeat de radio durante 5 segundos.
- MOX muestra TX real de interlock. TUNE sigue su estado informado y las órdenes
  confirmadas; ATU sigue `status` y `atu_enabled` del equipo.
- Requiere la nueva versión del puente `flex-mqtt` en la estación elegida.
  STN1 se ha validado con el FLEX real; STN2 requiere actualizar su contenedor.

```sh
node --test tests/transmit.test.mjs tests/weather.test.mjs
```

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
hay slice y muestra `--` solo en ese dato. Una banda recibida `0` muestra
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

### 1.6.0

- ATU: blanco en bypass, verde activado y rojo durante la sintonización, según el estado del FLEX.
- MUTE A/B: alterna el silencio de cada slice.
- RX A/B: selecciona el slice activo, sin cambiar su mute.
- TX A/B: selecciona el slice de transmisión, sin activar MOX.
- A=B: copia la frecuencia de A hacia B, sin cambiar modo ni audio.
- SPLIT: opción para silenciar B al activar; al desactivar conserva el audio.
- Todos los botones permiten seleccionar STN1/STN2 con el selector habitual.

Requiere actualizar los puentes flex-stn1 y flex-stn2. Los botones reflejan telemetría real y muestran SIN DATOS cuando falta el slice. No se crean slices con los nuevos botones; SPLIT conserva su función de creación de B.

### 1.6.1

ATU: pulsación breve inicia una sintonización, incluso estando ON. Mantener 700 ms o más y soltar desde ON pone el ATU en bypass. Una pulsación larga desde bypass no realiza ninguna acción. La orden se envía al soltar. No requiere cambios adicionales en el puente FLEX.

### 1.6.2

TX A: rojo cuando está seleccionado para transmitir y blanco cuando no está seleccionado.

### 1.6.3

TX B: rojo cuando está seleccionado para transmitir y blanco cuando no está seleccionado, igual que TX A.

### 1.6.4

MUTE A/B: rojo muteado, blanco sin mute. Pulsar en rojo desmutea; pulsar en blanco mutea.

### 1.7.0

SPLIT permite configurar volumen A/B (0–100) y balance A/B (0 izquierda, 50 centro, 100 derecha). Vacío conserva el valor actual. Se aplican al activar, antes de asignar TX B, con confirmación de cada orden. Mute B sigue siendo independiente; desactivar SPLIT no restaura el audio. Requiere actualizar los puentes FLEX.

### 1.7.1

Desactivar SPLIT centra ambos balances (50), selecciona RX A y TX A y cierra B. Se confirma cada paso antes del siguiente; no cierra B si falla la selección de A. No modifica los volúmenes. Requiere actualizar los puentes FLEX.

### 1.7.2

MUTE/RX/TX A/B distinguen ausencia de slice (blanco fijo, NO EXISTE) de falta de datos (parpadeo). MUTE: verde sin mute, rojo muteado. RX: verde seleccionado. TX: rojo seleccionado. RX/TX existentes sin seleccionar se muestran en gris. Requiere puentes actualizados con estado `absent`.
