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
    client.subscribe("tw1/deg");
    client.subscribe("tw2/deg");
    client.subscribe("tw1/mode");
    client.subscribe("tw2/mode");
    client.subscribe("tw1/setdeg");
    client.subscribe("tw2/setdeg");
    client.subscribe("tw1/nec");
    client.subscribe("tw2/nec");
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

            // Se colorea la selección del Stack de 10
            $("#stack101").text(json.stacks[10][1]['nombre'])
            $("#stack102").text(json.stacks[10][2]['nombre'])
            $("#stack103").text(json.stacks[10][3]['nombre'])
            if (ststn100 < 1) $("#stack101").removeClass("spanitemnd").removeClass("spanitemselected").addClass("spanitemne")
            else if (ststn101 == true) $("#stack101").removeClass("spanitemnd").removeClass("spanitemne").addClass("spanitemselected")
            else $("#stack101").removeClass("spanitemnd").removeClass("spanitemselected").removeClass("spanitemne")
            if (ststn100 < 2) $("#stack102").removeClass("spanitemnd").removeClass("spanitemselected").addClass("spanitemne")
            else if (ststn102 == true) $("#stack102").removeClass("spanitemnd").removeClass("spanitemne").addClass("spanitemselected")
            else $("#stack102").removeClass("spanitemnd").removeClass("spanitemselected").removeClass("spanitemne")
            if (ststn100 < 3) $("#stack103").removeClass("spanitemnd").removeClass("spanitemselected").addClass("spanitemne")
            else if (ststn103 == true) $("#stack103").removeClass("spanitemnd").removeClass("spanitemne").addClass("spanitemselected")
            else $("#stack103").removeClass("spanitemnd").removeClass("spanitemselected").removeClass("spanitemne")

            // Se colorea la selección del Stack de 15
            $("#stack151").text(json.stacks[15][1]['nombre'])
            $("#stack152").text(json.stacks[15][2]['nombre'])
            $("#stack153").text(json.stacks[15][3]['nombre'])
            if (ststn150 < 1) $("#stack151").removeClass("spanitemnd").removeClass("spanitemselected").addClass("spanitemne")
            else if (ststn151 == true) $("#stack151").removeClass("spanitemnd").removeClass("spanitemne").addClass("spanitemselected")
            else $("#stack151").removeClass("spanitemnd").removeClass("spanitemselected").removeClass("spanitemne")
            if (ststn150 < 2) $("#stack152").removeClass("spanitemnd").removeClass("spanitemselected").addClass("spanitemne")
            else if (ststn152 == true) $("#stack152").removeClass("spanitemnd").removeClass("spanitemne").addClass("spanitemselected")
            else $("#stack152").removeClass("spanitemnd").removeClass("spanitemselected").removeClass("spanitemne")
            if (ststn150 < 3) $("#stack153").removeClass("spanitemnd").removeClass("spanitemselected").addClass("spanitemne")
            else if (ststn153 == true) $("#stack153").removeClass("spanitemnd").removeClass("spanitemne").addClass("spanitemselected")
            else $("#stack153").removeClass("spanitemnd").removeClass("spanitemselected").removeClass("spanitemne")

            // Se colorea la selección del Stack de 20
            $("#stack201").text(json.stacks[20][1]['nombre'])
            $("#stack202").text(json.stacks[20][2]['nombre'])
            $("#stack203").text(json.stacks[20][3]['nombre'])
            if (ststn200 < 1) $("#stack201").removeClass("spanitemnd").removeClass("spanitemselected").addClass("spanitemne")
            else if (ststn201 == true) $("#stack201").removeClass("spanitemnd").removeClass("spanitemne").addClass("spanitemselected")
            else $("#stack201").removeClass("spanitemnd").removeClass("spanitemselected").removeClass("spanitemne")
            if (ststn200 < 2) $("#stack202").removeClass("spanitemnd").removeClass("spanitemselected").addClass("spanitemne")
            else if (ststn202 == true) $("#stack202").removeClass("spanitemnd").removeClass("spanitemne").addClass("spanitemselected")
            else $("#stack202").removeClass("spanitemnd").removeClass("spanitemselected").removeClass("spanitemne")
            if (ststn200 < 3) $("#stack203").removeClass("spanitemnd").removeClass("spanitemselected").addClass("spanitemne")
            else if (ststn203 == true) $("#stack203").removeClass("spanitemnd").removeClass("spanitemne").addClass("spanitemselected")
            else $("#stack203").removeClass("spanitemnd").removeClass("spanitemselected").removeClass("spanitemne")

            // Se colorea la selección del Stack de 40
            $("#stack401").text(json.stacks[40][1]['nombre'])
            $("#stack402").text(json.stacks[40][2]['nombre'])
            $("#stack403").text(json.stacks[40][3]['nombre'])
            if (ststn400 < 1) $("#stack401").removeClass("spanitemnd").removeClass("spanitemselected").addClass("spanitemne")
            else if (ststn401 == true) $("#stack401").removeClass("spanitemnd").removeClass("spanitemne").addClass("spanitemselected")
            else $("#stack401").removeClass("spanitemnd").removeClass("spanitemselected").removeClass("spanitemne")
            if (ststn400 < 2) $("#stack402").removeClass("spanitemnd").removeClass("spanitemselected").addClass("spanitemne")
            else if (ststn402 == true) $("#stack402").removeClass("spanitemnd").removeClass("spanitemne").addClass("spanitemselected")
            else $("#stack402").removeClass("spanitemnd").removeClass("spanitemselected").removeClass("spanitemne")
            if (ststn400 < 3) $("#stack403").removeClass("spanitemnd").removeClass("spanitemselected").addClass("spanitemne")
            else if (ststn403 == true) $("#stack403").removeClass("spanitemnd").removeClass("spanitemne").addClass("spanitemselected")
            else $("#stack403").removeClass("spanitemnd").removeClass("spanitemselected").removeClass("spanitemne")

            // Se colorea la selección del Stack de 80
            $("#stack801").text(json.stacks[80][1]['nombre'])
            $("#stack802").text(json.stacks[80][2]['nombre'])
            $("#stack803").text(json.stacks[80][3]['nombre'])
            if (ststn800 < 1) $("#stack801").removeClass("spanitemnd").removeClass("spanitemselected").addClass("spanitemne")
            else if (ststn801 == true) $("#stack801").removeClass("spanitemnd").removeClass("spanitemne").addClass("spanitemselected")
            else $("#stack801").removeClass("spanitemnd").removeClass("spanitemselected").removeClass("spanitemne")
            if (ststn800 < 2) $("#stack802").removeClass("spanitemnd").removeClass("spanitemselected").addClass("spanitemne")
            else if (ststn802 == true) $("#stack802").removeClass("spanitemnd").removeClass("spanitemne").addClass("spanitemselected")
            else $("#stack802").removeClass("spanitemnd").removeClass("spanitemselected").removeClass("spanitemne")
            if (ststn800 < 3) $("#stack803").removeClass("spanitemnd").removeClass("spanitemselected").addClass("spanitemne")
            else if (ststn803 == true) $("#stack803").removeClass("spanitemnd").removeClass("spanitemne").addClass("spanitemselected")
            else $("#stack803").removeClass("spanitemnd").removeClass("spanitemselected").removeClass("spanitemne")

            // Se colorea la selección del Stack de 160
            $("#stack1601").text(json.stacks[160][1]['nombre'])
            $("#stack1602").text(json.stacks[160][2]['nombre'])
            $("#stack1603").text(json.stacks[160][3]['nombre'])
            if (ststn1600 < 1) $("#stack1601").removeClass("spanitemnd").removeClass("spanitemselected").addClass("spanitemne")
            else if (ststn1601 == true) $("#stack1601").removeClass("spanitemnd").removeClass("spanitemne").addClass("spanitemselected")
            else $("#stack1601").removeClass("spanitemnd").removeClass("spanitemselected").removeClass("spanitemne")
            if (ststn1600 < 2) $("#stack1602").removeClass("spanitemnd").removeClass("spanitemselected").addClass("spanitemne")
            else if (ststn1602 == true) $("#stack1602").removeClass("spanitemnd").removeClass("spanitemne").addClass("spanitemselected")
            else $("#stack1602").removeClass("spanitemnd").removeClass("spanitemselected").removeClass("spanitemne")
            if (ststn1600 < 3) $("#stack1603").removeClass("spanitemnd").removeClass("spanitemselected").addClass("spanitemne")
            else if (ststn1603 == true) $("#stack1603").removeClass("spanitemnd").removeClass("spanitemne").addClass("spanitemselected")
            else $("#stack1603").removeClass("spanitemnd").removeClass("spanitemselected").removeClass("spanitemne")

        // Se pintan Mástiles 1 y 2
        } else if (message.destinationName == "tw1/deg") {
            tw1deg = parseInt(message.payloadString)
            if (tw1deg>360) {
                tw1deg = tw1deg - 360
                $('#tw1').text(tw1deg+"º")
                $("#tw1").addClass("twred")
            } else {
                $('#tw1').text(message.payloadString+"º")
                $('#tw1').removeClass("twred")
            }
        } else if (message.destinationName == "tw2/deg") {
            tw2deg = parseInt(message.payloadString)
            if (tw2deg>360) {
                tw2deg = tw2deg - 360
                $('#tw2').text(tw2deg+"º")
                $("#tw2").addClass("twred")
            } else {
                $('#tw2').text(message.payloadString+"º")
                $('#tw2').removeClass("twred")
            }
        } else if (message.destinationName == "tw1/mode") {
            $('#tw1mode').text(message.payloadString.toUpperCase())
            if (message.payloadString.toUpperCase() == "REM") {
                $("#tw1mode").addClass("spanitemselected");
            } else {
                $("#tw1mode").removeClass("spanitemselected");
            }
        } else if (message.destinationName == "tw2/mode") {
            $('#tw2mode').text(message.payloadString.toUpperCase())
            if (message.payloadString.toUpperCase() == "REM") {
                $("#tw2mode").addClass("spanitemselected");
            } else {
                $("#tw2mode").removeClass("spanitemselected");
            }
        } else if (message.destinationName == "tw1/setdeg") {
            $('#tw1set').text(message.payloadString+"º")
        } else if (message.destinationName == "tw2/setdeg") {
            $('#tw2set').text(message.payloadString+"º")
        } else if (message.destinationName == "tw1/nec") {
            if (message.payloadString == "CCW") {
                $('#tw1nec').text("↪️")
            } else if (message.payloadString == "CW") {
                $('#tw1nec').text("↩️")
            } else {
                $('#tw1nec').text("🆗")
            }
        } else if (message.destinationName == "tw2/nec") {
            if (message.payloadString == "CCW") {
                $('#tw2nec').text("↪️")
            } else if (message.payloadString == "CW") {
                $('#tw2nec').text("↩️")
            } else {
                $('#tw2nec').text("🆗")
            }
        }
    }
}
