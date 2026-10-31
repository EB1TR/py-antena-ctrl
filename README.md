# Instrucciones de Instalación

### Actualizar e instalar paquetes necesarios
sudo apt update<br>
sudo apt upgrade<br>
sudo apt install git curl<br>

### Instalar Docker
curl -fsSL https://get.docker.com -o get-docker.sh<br>
sudo chmod +x get-docker.sh<br>
sudo ./get-docker.sh<br>
sudo usermod -aG docker ${USER}<br>

### Instalar Docker Compose
sudo pip install --upgrade pip<br>
sudo pip install docker-compose<br>

### Clonación del repositorio
git clone https://github.com/EB1TR/py-antena-ctrl.git

### Edición de mqtt.js para que los clientes web conecten al socket
cd /home/pi/py-antena-ctrl<br>
nano nano static/mqtt.js<br>

<b>Ubicamos, y editamos, la siguiente línea:</b><br>
mqttHOST = "nnn.nnn.nnn.nnn"<br>
Donde nnn.nnn.nnn.nnn es la dirección IP del equipo donde corremos los contenedores.

### Construcción de las imágenes de Docker y arranque
cd /home/pi/py-antena-ctrl<br>
docker-compose build<br>
docker-compose up -d<br>

### Fuente de datos de las estaciones

La integración activa usa la API TCP y el stream VITA-49 UDP de dos equipos
FlexRadio. Sus direcciones y puertos se configuran en los servicios
`flex-stn1` y `flex-stn2` mediante `cfg/flex-stn1.json` y
`cfg/flex-stn2.json`, respectivamente. La conexión MQTT del servicio de
control se configura en `cfg/control.json`.

Los archivos de configuración técnica se montan en modo de solo lectura. Los
JSON existentes de estaciones, stacks y sixpack continúan separados de esta
configuración. Las configuraciones de los servicios auxiliares están en
`cfg/mosquitto/mosquitto.conf` y `cfg/nginx/default.conf`.

Cada servicio publica el estado real de transmisión como `stnN/tx`: `1` cuando
el estado `interlock` de FlexRadio es `TRANSMITTING` y `0` cuando es `READY`,
`RECEIVE`, `NOT_READY`, `TX_FAULT`, `TIMEOUT` o `STUCK_INPUT`.
Los estados transitorios `PTT_REQUESTED` y `UNKEY_REQUESTED` conservan el último
estado confirmado. Solo se procesa el campo `state` de los mensajes de estado
`interlock`: el `tx=1` de un slice selecciona el slice de transmisión y no
modifica TX/RX, ni lo hacen los campos de configuración como `rfpower`.

### Haz de las antenas en los mapas

Cada salida de cada banda en `cfg/stacks.json` admite `"haz"`: anchura total
del lóbulo principal a media potencia (−3 dB), en grados. Por ejemplo,
`"haz": 60` representa media potencia a ±30° respecto al rumbo del rotor.
Se admiten números mayores que 0 y hasta 360; 360 dibuja cobertura circular.
`null`, un campo ausente o un valor no válido utilizan el valor por defecto
de 45°, sin atribuir una medida real a la antena.

Los mapas utilizan la banda de la estación elegida en el selector STN1/STN2
y la salida cuyo `tw` corresponde al rotor, también cuando esa salida no está
activada. El haz se actualiza al cambiar la banda o la configuración, conservando
el rumbo y el color de selección. Sin estación o sin antena para esa banda se
utiliza el valor por defecto de 45°. Las antenas fijas (`tw: 0`) no tienen mapa de rotor.
El dibujo es una aproximación del lóbulo principal, no un diagrama de radiación
medido. Tras editar el archivo, reinicia el servicio `control` para publicar
la configuración actualizada.

### TukuDeck

El código fuente del plugin de Stream Deck forma parte de este repositorio en
`integrations/tukudeck`. Se construye e instala en el ordenador que ejecuta
Stream Deck y se comunica directamente con el broker MQTT del stack.

### Reboot
sudo shutdown -r now<br>

### Pérdida de datos de rotores

En las vistas nuevas de control y mapas, 5 segundos sin una posición válida
(`twN/deg`) ponen ese rotor en «Sin datos»: su panel parpadea y se oculta su haz.
Los rotores deben publicar la posición periódicamente incluso estando parados.
La siguiente posición válida recupera el indicador; el objetivo, modo y movimiento
se vuelven a mostrar cuando llegan sus respectivos mensajes. La desconexión MQTT
invalida inmediatamente las posiciones y mantiene el parpadeo de toda la interfaz.

### Órdenes MQTT de MOX y TUNE (FLEX)

El puente escucha `set/stn1/mox`, `set/stn1/tune` y los equivalentes de STN2.
Payload: `1` activa y `0` desactiva. Publicar sin retención. MOX utiliza
`xmit 1/0`; TUNE utiliza `transmit tune on/off` de la API TCP de FLEX:
https://github.com/flexradio/smartsdr-api-docs/wiki/TCPIP-xmit
https://github.com/flexradio/smartsdr-api-docs/wiki/TCPIP-transmit

Cada orden devuelve un JSON no retenido en `stnN/mox/result` o
`stnN/tune/result`, con `value` y `status`. `accepted` indica respuesta TCP
correcta del FLEX, no confirma emisión: el estado real sigue en `stnN/tx`
a partir de interlock. Los errores incluyen `error` (con `code` y `message`),
`timeout` (5 segundos), `disconnected`, `unavailable`, `send_error`,
`invalid_payload` y `retained_rejected`. No se encolan órdenes para reproducirlas
al reconectar. No se cambia la potencia configurada de MOX ni de TUNE.

Desde la carpeta del proyecto del servidor, reconstruir los puentes:

```sh
docker compose up -d --build flex-stn1 flex-stn2
```

Para probar STN1, observar primero los resultados y TX en una terminal:

```sh
docker compose exec mqtt mosquitto_sub -h localhost -v -t 'stn1/+/result' -t stn1/tx
```

Desde otra terminal, activar y desactivar cada función por separado, comprobando
SmartSDR y el estado real de transmisión entre órdenes:

```sh
docker compose exec mqtt mosquitto_pub -h localhost -t set/stn1/mox -m 1
docker compose exec mqtt mosquitto_pub -h localhost -t set/stn1/mox -m 0
docker compose exec mqtt mosquitto_pub -h localhost -t set/stn1/tune -m 1
docker compose exec mqtt mosquitto_pub -h localhost -t set/stn1/tune -m 0
```

Pruebas locales sin emitir RF: `python -m unittest discover -s tests -v`.
Los botones MOX, TUNE y ATU están disponibles en TukuDeck desde la versión 1.3.0.

ATU utiliza `set/stnN/atu` con payload `start` (ajuste automático) o `bypass`.
La confirmación llega a `stnN/atu/result`. Su estado real se publica en
`stnN/atu/state` (JSON de FLEX, con `status` y `atu_enabled`); `stnN/tune`
publica el estado TUNE informado por la radio. Los estados ATU y TUNE se retienen
para nuevos suscriptores; las órdenes y sus resultados no se retienen.
Referencia: https://github.com/flexradio/smartsdr-api-docs/wiki/TCPIP-atu

Validación real en STN1: MOX y TUNE aceptados en ambos sentidos, con TX/RX
confirmado por interlock. ATU informó `TUNE_IN_PROGRESS`, `TUNE_SUCCESSFUL` y finalmente
`TUNE_MANUAL_BYPASS`. Este último prevalece sobre `atu_enabled=1`.

La versión 1.3.1 renueva el heartbeat TX/RX ante respuestas TCP de la sesión
FLEX activa, aunque interlock no cambie. Tras reconectar espera un estado
interlock nuevo, para no conservar el TX de una sesión anterior.

### SPLIT configurable (versión 1.4.0)

El puente recibe `set/stnN/split` sin retención. Admite `0`/`1` con un
desplazamiento predeterminado de +1 kHz, o JSON como
`{"enabled":1,"offset_hz":2500}`. El desplazamiento admite enteros positivos o
negativos entre 1 y 100000 Hz de valor absoluto. El estado real se publica en
`stnN/split` (`0`, `1` o `unknown`); las respuestas van a `stnN/split/result`.

Al activar, se clona el receptor activo si no existe otro slice de su cliente,
y se sitúa el nuevo receptor en la frecuencia recibida más el desplazamiento.
Si ya existe un segundo slice del mismo cliente, se sintoniza ese slice.
La recepción permanece en el receptor original y TX se asigna al segundo.
Al desactivar, TX vuelve al receptor activo y se conserva el segundo slice.
Si hay varios clientes activos o varios candidatos no se elige uno arbitrariamente.
No se cambia SPLIT durante transmisión. Las órdenes no activan MOX ni TUNE.

El seguimiento de frecuencia y banda usa el receptor activo, no las frecuencias
recibidas de B. Se suscriben todos los slices para reflejar también cambios desde
SmartSDR. La operación utiliza la API documentada de FLEX:
https://github.com/flexradio/smartsdr-api-docs/wiki/TCPIP-slice

Desde 1.4.1, la creación de B especifica el mismo `pan` del receptor original.
Solo se reutilizan slices del mismo cliente y panadapter, conservando el
waterfall de recepción.

### Rotación de logs de Docker

Todos los servicios de `docker-compose.yaml` usan `json-file` con un tamaño
máximo de 10 MB por archivo y 3 archivos por contenedor (aproximadamente 30 MB
por servicio y 150 MB en total para los cinco servicios actuales).
Se conserva la consulta habitual con `docker compose logs`.

Para aplicar los límites a contenedores ya existentes hay que recrearlos:

```sh
docker compose up -d --no-build --force-recreate
```

La recreación interrumpe brevemente las conexiones y reemplaza los logs del
contenedor anterior; conserva una copia si necesitas investigar una incidencia.

### Control basado en feedback de relés

`svc/control/controller.py` separa las bandas solicitadas del estado confirmado
por las placas. No considera ejecutada una orden por el hecho de publicarla.
Denkovi se confirma con `SmartDEN_MQTT16R/<MAC>/Get/Rn` (`On`/`Off`);
Dingtian con `dtry/relay14475/out/rn` (`ON`/`OFF`). La alimentación de las radios
se lee de su feedback y solo se modifica cuando el usuario lo pide.

- Lee el estado al conectar y consulta las Denkovi cada 5 segundos, además de
  consultar tras enviar cambios. En Relays Settings debe estar habilitado MQTT
  en cada salida utilizada. Configura publicación por cambio y periódica a 5 s.
- Solo acciona relés cuyo estado real difiere del solicitado. Los que deben
  permanecer como están no se abren ni se vuelven a activar. Al cambiar de ruta,
  confirma el apagado de la anterior antes de cerrar la nueva. Un cambio de
  stack conserva la ruta y las antenas sin cambios y requiere RX confirmado
  en las estaciones conectadas; solo modifica ramas y balun que lo necesitan.
- Conserva exclusión de banda entre estaciones y del multiplexor compartido.
- No conmuta una estación en TX ni sin una lectura TX/RX reciente y no retenida.
- Solo corrige diferencias con el estado observado. Reintenta como máximo tres
  veces y publica el error si no se confirma; no genera ráfagas continuas.
- `stnN.band` mantiene la banda solicitada durante una conmutación; no pasa
  por N/A al cambiar un stack. `confirmed_band` conserva por separado la ruta
  física y `relay_status` indica si está alineada, pendiente o sin confirmar.
  Los estados de los relés y stacks reflejan el feedback recibido. `control/health` detalla los
  estados reales, deseados, pendientes, sin feedback y fallos de confirmación.
- `control/resync` permite releer y reintentar la alineación con lo solicitado.
  `update` solo solicita estado y nunca confirma ni acciona relés.

Para validarlo junto al servicio actual sin accionar salidas, ejecutar la imagen
candidata con `CONTROL_OBSERVE_ONLY=1`. En ese modo publica exclusivamente su
estado en `control/shadow/state` y `control/shadow/health`, además de consultas
GetStatus. No sustituye a `control` ni publica órdenes de conmutación.

El puente FLEX filtra las desapariciones transitorias de slices durante 2 s y
publica solo la banda actual, con heartbeat de 2 s: nunca repite primero la banda
anterior ni genera cientos de mensajes de «sin banda» durante la recreación.

### Banda MQTT sin segmento y logs de servicios

Los puentes publican un único entero en `stn1/band` y `stn2/band`: por ejemplo
`20`, `40` o `0` si no hay banda. El segmento no se publica ni se almacena.
El controlador y TukuDeck 1.5.0 leen la banda escalar; durante el despliegue
admiten mensajes antiguos tomando solo su primer elemento. La web consume la
banda numérica de `pytofront` y elimina la antigua indicación de segmento.

Los servicios escriben en stdout/stderr para seguirlos directamente:

```sh
docker compose logs -f control
docker compose logs -f flex-stn2
docker compose logs -f --tail=100 control flex-stn1 flex-stn2
```

Control registra solicitudes de relés, cambios de feedback, confirmaciones,
fallos y bandas solicitadas/confirmadas. FLEX registra conexiones, cambios de
banda, TX/RX y resultados de MOX/TUNE/ATU/SPLIT. Los heartbeats y el feedback
sin cambios no llenan el log con mensajes repetidos.

SPLIT admite opcionalmente `mute_b` (booleano) en su orden MQTT, por ejemplo
`{"enabled":1,"offset_hz":1000,"mute_b":true}`. Al activar aplica
`audio_mute=1` o `0` exclusivamente a B, antes de asignarle TX. Si no se incluye
`mute_b`, los clientes anteriores conservan su comportamiento de audio.
Al desactivar SPLIT se mantiene el estado de audio de B.

Comandos de slices (payload 0/1): `set/stnN/mutea`, `muteb`; selectores (payload 1): `rxa`, `rxb`, `txa`, `txb`, `a_eq_b`. El último copia únicamente la frecuencia A hacia B. Estado real en `stnN/<acción>` (0/1/unknown), resultado en `stnN/<acción>/result`. Se resuelve el identificador real por letra y cliente; las selecciones no activan transmisión y se rechazan durante TX, con slices ambiguos o ausentes y si el comando es retained.

### Despliegue completo 1.8.0 en Tuku

Incluye control con feedback, banda escalar, rotación de logs, web y TukuDeck 1.8.0.

```sh
cd /home/fabian/composes/py-antena-ctrl
git pull --ff-only
docker compose up -d --build --force-recreate
docker compose ps
docker compose logs -f --tail=100 control flex-stn1 flex-stn2
```

El plugin Stream Deck se instala por separado con el paquete 1.8.0. Consulta
[integrations/tukudeck/README.md](integrations/tukudeck/README.md) para el comportamiento
actual de RX/TX Maestro y de la tecla SPLIT especial.

### Configuración permanente y recuperación del estado de control

El formato MQTT (`pytofront` y `control/health`) se mantiene. Las vistas antiguas,
`stack-v2`, los mapas azimutales y TukuDeck siguen recibiendo la misma estructura.
Esta reorganización no implementa todavía el protocolo de comunicación reducido.

```text
cfg/
  control.json                  conexión MQTT del servicio
  control/
    installation.json           estaciones, antenas, rotores, haces y relés
    initial-state.json          valores iniciales cuando no hay estado guardado
data/
  control/
    state.json                  último estado operativo y observaciones
```

`installation.json` contiene la configuración permanente: nombres, salidas por
banda, rotor y haz de cada antena, cableado de relés, multiplexación y alimentación.
No contiene el modo automático, banda elegida ni selección de antenas.
`initial-state.json` define esos valores de arranque; no se reescribe al operar.
Los ficheros `.example.json` son ejemplos versionados; los ficheros reales y el
estado operativo son locales y están excluidos de Git.

Para convertir **los ficheros de cada instalación**, sin borrarlos ni sobrescribir
una configuración nueva existente:

```sh
python3 svc/control/config_layout.py cfg
```

La conversión usa `stn1.json`, `stn2.json`, `stacks.json` y `sixpack.json`. Mientras
no exista el nuevo formato, el cargador admite el anterior. Si existe solo parte
del nuevo formato o es inválido, falla explícitamente: no ignora el error ni usa
silenciosamente otra configuración. Los ejemplos permiten preparar una instalación
nueva; no se copian automáticamente sobre la configuración de Tuku.

Control guarda `data/control/state.json` solo cuando cambia su contenido,
mediante un temporal en el mismo directorio, `fsync` y reemplazo atómico. Compose
mantiene `cfg` en solo lectura y da escritura únicamente al directorio de estado.
El guardado comienza después de recibir el feedback completo de los relés y no
se ejecuta en modo de observación. `CONTROL_STATE_PATH` permite cambiar la ruta.
Un estado existente corrupto o incompatible impide el arranque y no se sustituye
por valores iniciales silenciosamente.

Se recuperan AUTO/MANUAL, bandas solicitadas, selección de salidas en todas las
bandas y bandas previamente preparadas. Se guardan también alimentación observada,
relés, bandas y TX recibidos, diagnóstico y órdenes de alimentación pendientes
para conservar el contexto. Esas observaciones **no se restauran como confirmaciones
ni se reproducen como órdenes de alimentación**: al arrancar se relee el hardware,
se esperan datos frescos de radio y se mantienen los bloqueos de TX. En AUTO, la
banda real nueva del FLEX tiene prioridad sobre la última banda guardada.
Si los relés ya coinciden, no se conmutan innecesariamente. Las selecciones
recuperadas no se sustituyen por el feedback inicial durante su reconciliación.

Esto conserva el estado del servicio de antenas; no guarda ni restaura los slices,
frecuencias o audio internos del FLEX ni la posición de los rotores. Las opciones
de cada botón de Stream Deck continúan almacenadas por Stream Deck.

### Protocolo de consumidores 2 / TukuDeck 1.9.0

Control separa configuración permanente y estado operativo en MQTT:

- `control/config`: catálogo retenido (estaciones, antenas por banda, nombres,
  rotores y haces). Solo se publica cuando cambia o al reconectar control.
- `pytofront`: estado compacto retenido, solo cuando cambia. Contiene referencia
  al catálogo, identificador de sesión, revisión, estaciones, selecciones por
  banda y un resumen de sincronización. No incluye cableado ni diagnóstico completo.
- `control/heartbeat`: señal de vida no retenida cada 2 s y tras cambios, con la
  sesión y revisión actuales. No repite el catálogo ni el estado.
- `control/availability`: online/offline retenido, con Last Will MQTT.
- `control/health`: diagnóstico detallado retenido, solo cuando cambia. No lo
  reciben las interfaces normales. `update` permite solicitar una republicación.

La web antigua, stack-v2, stack-azimut y TukuDeck comparten el decodificador
`static/control-state.js`. Reconstruye su modelo de presentación sin duplicar el
catálogo en cada actualización. Un catálogo/estado retenido no confirma que el
servicio esté vivo: se espera un heartbeat de la misma sesión y una revisión
compatible. Tras 5 s sin señal, o al recibir offline/desconectarse, se invalidan
los controles de antenas. Los datos FLEX y rotores conservan sus circuitos de
actualización y caducidad independientes. Las selecciones sin feedback se
transmiten como null, no como un OFF confirmado.

Para actualizar: desplegar control y los archivos web juntos, recargar las vistas
abiertas e instalar TukuDeck 1.9.0. Las interfaces nuevas aceptan el paquete antiguo
para poder actualizarlas antes que control. Los consumidores antiguos necesitan
actualizarse para interpretar el protocolo 2. No requiere cambiar los puentes FLEX.
El estado completo sigue guardándose en disco; se reduce lo enviado por red.
