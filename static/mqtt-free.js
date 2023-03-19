clientID = "web"
mqttHOST = "192.168.33.200"
clientID += new Date().getUTCMilliseconds()
client = new Paho.MQTT.Client(mqttHOST, Number(9001), clientID);

client.onConnectionLost = onConnectionLost;
client.onMessageArrived = onMessageArrived;
client.onFailure = onConnectionLost;

client.connect({
    onSuccess:onConnect,
    onFailure:onConnectionLost
})

function onConnect() {
    console.log("Connectado a MQTT.");
    $('#contenor').removeClass("FinFout")
    client.subscribe("pytofront");
    console.log("Suscrito a topics MQTT.");
    message = new Paho.MQTT.Message('0');
    message.destinationName = "update";
    client.send(message);
    console.log("Información inicial solicitada.")
}

function onConnectionLost(responseObject) {
  if (responseObject.errorCode !== 0) {
    console.log("Conexión perdida a MQTT:"+responseObject.errorMessage);
  }
  $('#contenor').addClass("FinFout")
}

function send_command(comm, dato){
  message = new Paho.MQTT.Message(String(dato));
  message.destinationName = comm;
  client.send(message);
}

function onMessageArrived(message) {
    if (message.destinationName == "pytofront") {
        json = JSON.parse(message.payloadString)
        if (json.stn1 != undefined) {
            json = JSON.parse(message.payloadString)

            ststn100 = json.stacks[10]['salidas']
            ststn101 = json.stacks[10][1]['estado']
            ststn102 = json.stacks[10][2]['estado']
            ststn103 = json.stacks[10][3]['estado']

            ststn150 = json.stacks[15]['salidas']
            ststn151 = json.stacks[15][1]['estado']
            ststn152 = json.stacks[15][2]['estado']
            ststn153 = json.stacks[15][3]['estado']

            ststn200 = json.stacks[20]['salidas']
            ststn201 = json.stacks[20][1]['estado']
            ststn202 = json.stacks[20][2]['estado']
            ststn203 = json.stacks[20][3]['estado']

            ststn400 = json.stacks[40]['salidas']
            ststn401 = json.stacks[40][1]['estado']
            ststn402 = json.stacks[40][2]['estado']
            ststn403 = json.stacks[40][3]['estado']

            ststn800 = json.stacks[80]['salidas']
            ststn801 = json.stacks[80][1]['estado']
            ststn802 = json.stacks[80][2]['estado']
            ststn803 = json.stacks[80][3]['estado']

            ststn1600 = json.stacks[160]['salidas']
            ststn1601 = json.stacks[160][1]['estado']
            ststn1602 = json.stacks[160][2]['estado']
            ststn1603 = json.stacks[160][3]['estado']

            // Se pinta el nombre de antena de cada posición Stack en la banda seleccionada en la STN1
            $("#stack101").text(json.stacks[10][1]['nombre'])
            $("#stack102").text(json.stacks[10][2]['nombre'])
            $("#stack103").text(json.stacks[10][3]['nombre'])
            // Se colorea la selección del Stack de la STN1
            if (ststn101 == true) $("#stack101").removeClass("spanitemnd").addClass("spanitemselected")
            else $("#stack101").removeClass("spanitemnd").removeClass("spanitemselected")
            if (ststn102 == true) $("#stack102").removeClass("spanitemnd").addClass("spanitemselected")
            else $("#stack102").removeClass("spanitemnd").removeClass("spanitemselected")
            if (ststn103 == true) $("#stack103").removeClass("spanitemnd").addClass("spanitemselected")
            else $("#stack103").removeClass("spanitemnd").removeClass("spanitemselected")

            // Se pinta el nombre de antena de cada posición Stack en la banda seleccionada en la STN1
            $("#stack151").text(json.stacks[15][1]['nombre'])
            $("#stack152").text(json.stacks[15][2]['nombre'])
            $("#stack153").text(json.stacks[15][3]['nombre'])
            // Se colorea la selección del Stack de la STN1
            if (ststn151 == true) $("#stack151").removeClass("spanitemnd").addClass("spanitemselected")
            else $("#stack151").removeClass("spanitemnd").removeClass("spanitemselected")
            if (ststn152 == true) $("#stack152").removeClass("spanitemnd").addClass("spanitemselected")
            else $("#stack152").removeClass("spanitemnd").removeClass("spanitemselected")
            if (ststn153 == true) $("#stack153").removeClass("spanitemnd").addClass("spanitemselected")
            else $("#stack153").removeClass("spanitemnd").removeClass("spanitemselected")

            // Se pinta el nombre de antena de cada posición Stack en la banda seleccionada en la STN1
            $("#stack201").text(json.stacks[20][1]['nombre'])
            $("#stack202").text(json.stacks[20][2]['nombre'])
            $("#stack203").text(json.stacks[20][3]['nombre'])
            // Se colorea la selección del Stack de la STN1
            if (ststn201 == true) $("#stack201").removeClass("spanitemnd").addClass("spanitemselected")
            else $("#stack201").removeClass("spanitemnd").removeClass("spanitemselected")
            if (ststn202 == true) $("#stack202").removeClass("spanitemnd").addClass("spanitemselected")
            else $("#stack202").removeClass("spanitemnd").removeClass("spanitemselected")
            if (ststn203 == true) $("#stack203").removeClass("spanitemnd").addClass("spanitemselected")
            else $("#stack203").removeClass("spanitemnd").removeClass("spanitemselected")


            // Se pinta el nombre de antena de cada posición Stack en la banda seleccionada en la STN1
            $("#stack401").text(json.stacks[40][1]['nombre'])
            $("#stack402").text(json.stacks[40][2]['nombre'])
            $("#stack403").text(json.stacks[40][3]['nombre'])
            // Se colorea la selección del Stack de la STN1
            if (ststn401 == true) $("#stack401").removeClass("spanitemnd").addClass("spanitemselected")
            else $("#stack401").removeClass("spanitemnd").removeClass("spanitemselected")
            if (ststn402 == true) $("#stack402").removeClass("spanitemnd").addClass("spanitemselected")
            else $("#stack402").removeClass("spanitemnd").removeClass("spanitemselected")
            if (ststn403 == true) $("#stack403").removeClass("spanitemnd").addClass("spanitemselected")
            else $("#stack403").removeClass("spanitemnd").removeClass("spanitemselected")

            // Se pinta el nombre de antena de cada posición Stack en la banda seleccionada en la STN1
            $("#stack801").text(json.stacks[80][1]['nombre'])
            $("#stack802").text(json.stacks[80][2]['nombre'])
            $("#stack803").text(json.stacks[80][3]['nombre'])
            // Se colorea la selección del Stack de la STN1
            if (ststn801 == true) $("#stack801").removeClass("spanitemnd").addClass("spanitemselected")
            else $("#stack801").removeClass("spanitemnd").removeClass("spanitemselected")
            if (ststn802 == true) $("#stack802").removeClass("spanitemnd").addClass("spanitemselected")
            else $("#stack802").removeClass("spanitemnd").removeClass("spanitemselected")
            if (ststn803 == true) $("#stack803").removeClass("spanitemnd").addClass("spanitemselected")
            else $("#stack803").removeClass("spanitemnd").removeClass("spanitemselected")

            // Se pinta el nombre de antena de cada posición Stack en la banda seleccionada en la STN1
            $("#stack1601").text(json.stacks[160][1]['nombre'])
            $("#stack1602").text(json.stacks[160][2]['nombre'])
            $("#stack1603").text(json.stacks[160][3]['nombre'])
            // Se colorea la selección del Stack de la STN1
            if (ststn1601 == true) $("#stack1601").removeClass("spanitemnd").addClass("spanitemselected")
            else $("#stack1601").removeClass("spanitemnd").removeClass("spanitemselected")
            if (ststn1602 == true) $("#stack1602").removeClass("spanitemnd").addClass("spanitemselected")
            else $("#stack1602").removeClass("spanitemnd").removeClass("spanitemselected")
            if (ststn1603 == true) $("#stack1603").removeClass("spanitemnd").addClass("spanitemselected")
            else $("#stack1603").removeClass("spanitemnd").removeClass("spanitemselected")
        }
    }
}
