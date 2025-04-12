clientID = "web"
mqttHOST = "192.168.88.10"
clientID += new Date().getUTCMilliseconds()
client = new Paho.MQTT.Client(mqttHOST, Number(9001), clientID);

client.onConnectionLost = onConnectionLost;
client.onMessageArrived = onMessageArrived;
client.onFailure = onConnectionLost;

client.connect({
    onSuccess:onConnect,
    onFailure:onConnectionLost
});

function createAverageCalculator(n) {
    const values = [];
    return function (newNumber) {
      // Añadir nuevo número al array
      values.push(newNumber);
      // Si hay más de n elementos, quitar el más antiguo
      if (values.length > n) {
        values.shift();
      }
      // Calcular el promedio
      const sum = values.reduce((acc, val) => acc + val, 0);
      return sum / values.length;
    };
  }
  
  function createMaxTracker(n) {
    const values = [];
    return function (newNumber) {
      // Añadir nuevo número al array
      values.push(newNumber);
      // Si hay más de n elementos, quitar el más antiguo
      if (values.length > n) {
        values.shift();
      }
      // Calcular el valor máximo
      return Math.max(...values);
    };
  }
  
  // Ejemplo de uso:
  const maxpwrr1 = createMaxTracker(20);
  const maxpwrr2 = createMaxTracker(20);
  
  const avgpwrr1 = createAverageCalculator(8);
  const avgpwrr2 = createAverageCalculator(8);
  const avgswrr1 = createAverageCalculator(8);
  const avgswrr2 = createAverageCalculator(8);


function onConnect() {
    console.log("Connectado a MQTT.");
    $('#contenor').removeClass("FinFout")
    client.subscribe("pytofront");
    client.subscribe("stn1/#");
    client.subscribe("stn2/#");
    client.subscribe("tw1/#");
    client.subscribe("tw2/#");
    client.subscribe("tw3/#");
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
        $('#stn1-r1-qrg').text((message.payloadString/100).toFixed(1)+" kHz")
    } else if (message.destinationName == "stn1/pwr") {
        let PWRAR1 = avgpwrr1(message.payloadString/1); // 10.0
        let PWRPR1 = maxpwrr1(message.payloadString/1)
        $('#stn1-r1-pwr').text((PWRAR1).toFixed(1)+"Wa")
        if (PWRAR1>80) {
            $("#stn1-r1-pwr").addClass("twgreen")
        //} else if (PWRAR1>70) {
        //    $('#stn1-r1-pwr').removeClass("twored").addClass("tworange")
        } else {
            $('#stn1-r1-pwr').removeClass("twgreen")
        }
        $('#stn1-r1-pwrp').text((PWRPR1).toFixed(1)+"Wp")
        if (PWRPR1>95) {
            $("#stn1-r1-pwrp").addClass("twgreen")
        //} else if (PWRPR1>90) {
        //    $('#stn1-r1-pwrp').removeClass("twored").addClass("tworange")
        } else {
            $('#stn1-r1-pwrp').removeClass("twgreen")
        }
    } else if (message.destinationName == "stn1/swr") {
        let ROER1 = avgswrr1(message.payloadString/1)
        $('#stn1-r1-swr').text((ROER1).toFixed(1)+":1")
        if (ROER1>2) {
            $("#stn1-r1-swr").addClass("twred")
        } else if (ROER1>1.5) {
            $('#stn1-r1-swr').removeClass("twored").addClass("tworange")
        } else {
            $('#stn1-r1-swr').removeClass("twred").removeClass("tworange")
        }
    } else if (message.destinationName == "stn1/tensiona") {
        $('#stn1-r1-va').text((message.payloadString/1).toFixed(1)+"V")
        if ((message.payloadString/1)<13) {
            $("#stn1-r1-va").addClass("twred")
        } else {
            $('#stn1-r1-va').removeClass("twred")
        }
    } else if (message.destinationName == "stn1/temp") {
        $('#stn1-r1-temp').text((message.payloadString/1).toFixed(1)+"ºC")
        if ((message.payloadString/1)>40) {
            $("#stn1-r1-temp").addClass("twred")
        } else {
            $('#stn1-r1-temp').removeClass("twred")
        }
    } else if (message.destinationName == "stn1/fun") {
        $('#stn1-r1-fun').text((message.payloadString)+"rpm")

    } else if (message.destinationName == "stn2/qrg") {
        $('#stn2-r1-qrg').text((message.payloadString/100).toFixed(1)+" kHz")
    } else if (message.destinationName == "stn2/pwr") {
        let PWRAR2 = avgpwrr2(message.payloadString/1); // 10.0
        let PWRPR2 = maxpwrr2(message.payloadString/1)
        $('#stn2-r1-pwr').text((PWRAR2).toFixed(1)+"Wa")
        if (PWRAR2>80) {
            $("#stn2-r1-pwr").addClass("twgreen")
        //} else if (PWRAR2>70) {
        //    $('#stn2-r1-pwr').removeClass("twored").addClass("tworange")
        } else {
            $('#stn2-r1-pwr').removeClass("twgreen")
        }
        $('#stn2-r1-pwrp').text((PWRPR2).toFixed(1)+"Wp")
        if (PWRPR2>95) {
            $("#stn2-r1-pwrp").addClass("twgreen")
        //} else if (PWRPR2>90) {
        //    $('#stn2-r1-pwrp').removeClass("twored").addClass("tworange")
        } else {
            $('#stn2-r1-pwrp').removeClass("twgreen")
        }
    } else if (message.destinationName == "stn2/swr") {
        let ROER2 = avgswrr2(message.payloadString/1)
        $('#stn2-r1-swr').text((ROER2).toFixed(1)+":1")
        if (ROER2>2) {
            $("#stn2-r1-swr").addClass("twred")
        } else if (ROER2>1.5) {
            $('#stn2-r1-swr').removeClass("twored").addClass("tworange")
        } else {
            $('#stn2-r1-swr').removeClass("twred").removeClass("tworange")
        }
    } else if (message.destinationName == "stn2/tensiona") {
        $('#stn2-r1-va').text((message.payloadString/1).toFixed(1)+"V")
        if ((message.payloadString/1)<13) {
            $("#stn2-r1-va").addClass("twred")
        } else {
            $('#stn2-r1-va').removeClass("twred")
        }
    } else if (message.destinationName == "stn2/temp") {
        $('#stn2-r1-temp').text((message.payloadString/1).toFixed(1)+"ºC")
        if ((message.payloadString/1)>40) {
            $("#stn2-r1-temp").addClass("twred")
        } else {
            $('#stn2-r1-temp').removeClass("twred")
        }
    } else if (message.destinationName == "stn2/fun") {
        $('#stn2-r1-fun').text((message.payloadString)+"rpm")

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
    } else if (message.destinationName == "tw3/deg") {
        tw3deg = parseInt(message.payloadString)
        if (tw3deg>360) {
            tw3deg = tw3deg - 360
            $('#tw3').text(tw3deg+"º")
            $("#tw3").addClass("twred")
        } else {
            $('#tw3').text(tw3deg+"º")
            $('#tw3').removeClass("twred")
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
    }  else if (message.destinationName == "tw3/mode") {
        $('#tw3mode').text(message.payloadString.toUpperCase())
        if (message.payloadString.toUpperCase() == "REM") {
            $("#tw3mode").addClass("spanitemselected");
        } else {
            $("#tw3mode").removeClass("spanitemselected");
        }
    } else if (message.destinationName == "tw1/setdeg") {
        $('#tw1set').text(message.payloadString+"º")
    } else if (message.destinationName == "tw2/setdeg") {
        $('#tw2set').text(message.payloadString+"º")
    } else if (message.destinationName == "tw3/setdeg") {
        $('#tw3set').text(message.payloadString+"º")
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
    } else if (message.destinationName == "tw3/nec") {
        if (message.payloadString == "CCW") {
            $('#tw3nec').text("↪️")
        } else if (message.payloadString == "CW") {
            $('#tw3nec').text("↩️")
        } else {
            $('#tw3nec').text("🆗")
        }
    } else if (message.destinationName == "pytofront") {
        json = JSON.parse(message.payloadString)
        if (json.stn1 != undefined) {
            json = JSON.parse(message.payloadString)
            bstn1 = "#stn1-b"+json.stn1.band
            bstn2 = "#stn2-b"+json.stn2.band

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

            // Se pinta la utilización de la TW3 por parte de la STN2
            if ((json.stacks[json.stn2.band][1]['tw'] == 3 && ststn21 == true) ||
                (json.stacks[json.stn2.band][2]['tw'] == 3 && ststn22 == true) ||
                (json.stacks[json.stn2.band][3]['tw'] == 3 && ststn23 == true)) {
                $("#tw3stn1").show()
            } else {
                $("#tw3stn1").hide()
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

            // Se pinta la utilización de la TW3 por parte de la STN2
            if ((json.stacks[json.stn2.band][1]['tw'] == 3 && ststn21 == true) ||
                (json.stacks[json.stn2.band][2]['tw'] == 3 && ststn22 == true) ||
                (json.stacks[json.stn2.band][3]['tw'] == 3 && ststn23 == true)) {
                $("#tw3stn2").show()
            } else {
                $("#tw3stn2").hide()
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
