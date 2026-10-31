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
