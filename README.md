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

### Reboot
sudo shutdown -r now<br>
