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
});

function onConnect() {
    console.log("Connectado a MQTT.");
    $('#contenor').removeClass("FinFout")
    client.subscribe("pytofront");
    client.subscribe("stn1/qrg");
    client.subscribe("stn2/qrg");
    client.subscribe("stn1/mode");
    client.subscribe("stn2/mode");
    client.subscribe("stn1/op");
    client.subscribe("stn2/op");
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
    if (message.destinationName == "stn1/qrg") {
        $('#stn1-r1-qrg').text((message.payloadString/100).toFixed(2))
    } else if (message.destinationName == "stn2/qrg") {
        $('#stn2-r1-qrg').text((message.payloadString/100).toFixed(2))
    } else if (message.destinationName == "stn1/mode") {
        $('#stn1-r1-mode').text(message.payloadString)
    } else if (message.destinationName == "stn2/mode") {
        $('#stn2-r1-mode').text(message.payloadString)
    } else if (message.destinationName == "stn1/op") {
        $('#stn1-op').text(message.payloadString)
    } else if (message.destinationName == "stn2/op") {
        $('#stn2-op').text(message.payloadString)
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
    } else {
        json = JSON.parse(message.payloadString)
        if (json.stn1 != undefined) {
            json = JSON.parse(message.payloadString)
            bstn1 = "#stn1-b"+json.stn1.band
            bstn2 = "#stn2-b"+json.stn2.band

            console.log(bstn1)

            asstn1 = json.stn1.auto
            asstn2 = json.stn2.auto

            ststn10 = json.stacks[json.stn1.band]['salidas']
            ststn11 = json.stacks[json.stn1.band][1]['estado']
            ststn12 = json.stacks[json.stn1.band][2]['estado']
            ststn13 = json.stacks[json.stn1.band][3]['estado']

            ststn20 = json.stacks[json.stn2.band]['salidas']
            ststn21 = json.stacks[json.stn2.band][1]['estado']
            ststn22 = json.stacks[json.stn2.band][2]['estado']
            ststn23 = json.stacks[json.stn2.band][3]['estado']

            // Se pinta la utilización de la TW1 por parte de la STN1
            if ((json.stacks[json.stn1.band][1]['tw'] == 1 && ststn11 == true) ||
                (json.stacks[json.stn1.band][2]['tw'] == 1 && ststn12 == true) ||
                (json.stacks[json.stn1.band][3]['tw'] == 1 && ststn13 == true)) {
                $("#tw1stn1").show()
            } else {
                $("#tw1stn1").hide()
            }

            // Se pinta la utilización de la TW2 por parte de la STN1
            if ((json.stacks[json.stn1.band][1]['tw'] == 2 && ststn11 == true) ||
                (json.stacks[json.stn1.band][2]['tw'] == 2 && ststn12 == true) ||
                (json.stacks[json.stn1.band][3]['tw'] == 2 && ststn13 == true)) {
                $("#tw2stn1").show()
            } else {
                $("#tw2stn1").hide()
            }

            // Se pinta la utilización de la TW1 por parte de la STN2
            if ((json.stacks[json.stn2.band][1]['tw'] == 1 && ststn21 == true) ||
                (json.stacks[json.stn2.band][2]['tw'] == 1 && ststn22 == true) ||
                (json.stacks[json.stn2.band][3]['tw'] == 1 && ststn23 == true)) {
                $("#tw1stn2").show()
            } else {
                $("#tw1stn2").hide()
            }

            // Se pinta la utilización de la TW2 por parte de la STN2
            if ((json.stacks[json.stn2.band][1]['tw'] == 2 && ststn21 == true) ||
                (json.stacks[json.stn2.band][2]['tw'] == 2 && ststn22 == true) ||
                (json.stacks[json.stn2.band][3]['tw'] == 2 && ststn23 == true)) {
                $("#tw2stn2").show()
            } else {
                $("#tw2stn2").hide()
            }

            // Se resetea el estado de banda seleccionada
            $("[id^=stn1-b]").removeClass("spanitemselected");
            $("[id^=stn2-b]").removeClass("spanitemselected");

            $(bstn1).addClass("spanitemselected")
            $(bstn2).addClass("spanitemselected")


            // Se resetea el estado AUTO ON/OFF de la conmutación
            $("#stn1-as").removeClass("spanitemselected");
            $("#stn2-as").removeClass("spanitemselected");

            // Se colorea AUTO ON/OFF en la STN1
            if (asstn1 == true) $("#stn1-as").addClass("spanitemselected")

            // Se colorea AUTO ON/OFF en la STN2
            if (asstn2 == true) $("#stn2-as").addClass("spanitemselected")

            $('#stn1-n').text(json.stn1.netbios)
            $('#stn2-n').text(json.stn2.netbios)

            // Se colorea el estado de cada entrada del Stack en la banda seleccionada en la STN1
            $("#stn1-stack1").addClass("spanitemnd")
            $("#stn1-stack2").addClass("spanitemnd")
            $("#stn1-stack3").addClass("spanitemnd")

            // Se pinta el nombre de antena de cada posición Stack en la banda seleccionada en la STN1
            $("#stn1-stack1").text(json.stacks[json.stn1.band][1]['nombre'])
            $("#stn1-stack2").text(json.stacks[json.stn1.band][2]['nombre'])
            $("#stn1-stack3").text(json.stacks[json.stn1.band][3]['nombre'])

            // Se colorea la selección del Stack de la STN1
            if (ststn10 == 3) {
                if (ststn11 == true) $("#stn1-stack1").removeClass("spanitemnd").addClass("spanitemselected")
                else $("#stn1-stack1").removeClass("spanitemnd").removeClass("spanitemselected")
                if (ststn12 == true) $("#stn1-stack2").removeClass("spanitemnd").addClass("spanitemselected")
                else $("#stn1-stack2").removeClass("spanitemnd").removeClass("spanitemselected")
                if (ststn13 == true) $("#stn1-stack3").removeClass("spanitemnd").addClass("spanitemselected")
                else $("#stn1-stack3").removeClass("spanitemnd").removeClass("spanitemselected")
            } else if (ststn10 == 2) {
                if (ststn11 == true) $("#stn1-stack1").removeClass("spanitemnd").addClass("spanitemselected")
                else $("#stn1-stack1").removeClass("spanitemnd").removeClass("spanitemselected")
                if (ststn12 == true) $("#stn1-stack2").removeClass("spanitemnd").addClass("spanitemselected")
                else $("#stn1-stack2").removeClass("spanitemnd").removeClass("spanitemselected")
            } else if (ststn10 == 1) {
                if (ststn11 == true) $("#stn1-stack1").removeClass("spanitemnd").addClass("spanitemselected")
                else $("#stn1-stack1").removeClass("spanitemnd").removeClass("spanitemselected")
            }
            // Se colorea el estado de cada entrada del Stack en la banda seleccionada en la STN2
            $("#stn2-stack1").addClass("spanitemnd")
            $("#stn2-stack2").addClass("spanitemnd")
            $("#stn2-stack3").addClass("spanitemnd")

            // Se pinta el nombre de antena de cada posición Stack en la banda seleccionada en la STN2
            $("#stn2-stack1").text(json.stacks[json.stn2.band][1]['nombre'])
            $("#stn2-stack2").text(json.stacks[json.stn2.band][2]['nombre'])
            $("#stn2-stack3").text(json.stacks[json.stn2.band][3]['nombre'])

            // Se colorea la selección del Stack de la STN1
            if (ststn20 == 3) {
                if (ststn21 == true) $("#stn2-stack1").removeClass("spanitemnd").addClass("spanitemselected")
                else $("#stn2-stack1").removeClass("spanitemnd").removeClass("spanitemselected")
                if (ststn22 == true) $("#stn2-stack2").removeClass("spanitemnd").addClass("spanitemselected")
                else $("#stn2-stack2").removeClass("spanitemnd").removeClass("spanitemselected")
                if (ststn23 == true) $("#stn2-stack3").removeClass("spanitemnd").addClass("spanitemselected")
                else $("#stn2-stack3").removeClass("spanitemnd").removeClass("spanitemselected")
            } else if (ststn20 == 2) {
                if (ststn21 == true) $("#stn2-stack1").removeClass("spanitemnd").addClass("spanitemselected")
                else $("#stn2-stack1").removeClass("spanitemnd").removeClass("spanitemselected")
                if (ststn22 == true) $("#stn2-stack2").removeClass("spanitemnd").addClass("spanitemselected")
                else $("#stn2-stack2").removeClass("spanitemnd").removeClass("spanitemselected")
            } else if (ststn20 == 1) {
                if (ststn21 == true) $("#stn2-stack1").removeClass("spanitemnd").addClass("spanitemselected")
                else $("#stn2-stack1").removeClass("spanitemnd").removeClass("spanitemselected")
            }

            // Se elimina la indicación de segmento de la STN1 si no se está en una banda que los utilice
            if (json.stn1.segmento != 0 && json.stacks[json.stn1.band][1]['estado']) {
                $("#stn1-segmento").removeClass("spanitemnd").text(json.stn1.segmento)
            }

            // Se elimina la indicación de segmento de la STN2 si no se está en una banda que los utilice
            if (json.stn2.segmento != 0 && json.stacks[json.stn2.band][1]['estado']) {
                $("#stn2-segmento").removeClass("spanitemnd").text(json.stn2.segmento)
            }
        }
    }
}
