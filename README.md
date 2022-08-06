# Intrucciones de Instalación

### Actualizar e instalar paquetes necesarios
sudo apt update<br>
sudo apt upgrade<br>
sudo apt install git curl libffi-dev libssl-dev python3-dev python3 python3-pip virtualenv<br>y

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

### Preparamos entornos virtuales en el Host
cd /home/pi<br>
mkdir venvs<br>
mkdir venvs/host_cmd<br>
mkdir venvs/host_status<br>
virtualenv venvs/host_cmd<br>
virtualenv venvs/host_status<br>
source venvs/host_cmd/bin/activate<br>
pip install --upgrade pip<br>
pip install paho-mqtt<br>
deactivate<br>
source venvs/host_status/bin/activate<br>
pip install --upgrade pip<br>
pip install paho-mqtt psutil<br>
deactivate<br>

### Modificamos rc.local para lanzar tareas en el Host
sudo cp py-antena-ctrl/resources/rc.local /etc/rc.local<br>

### Contrucción de las imagenes de Docker y arranque
cd /home/pi/py-antena-ctrl<br>
docker-compose build<br>
docker-compose up -d<br>

### Reboot
sudo shutdown -r now<br>
