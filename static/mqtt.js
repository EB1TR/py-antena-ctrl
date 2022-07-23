clientID = "web"
clientID += new Date().getUTCMilliseconds()
client = new Paho.MQTT.Client("192.168.88.10", Number(9001), clientID);

client.onConnectionLost = onConnectionLost;
client.onMessageArrived = onMessageArrived;

client.connect({onSuccess:onConnect});

function onConnect() {
  console.log("Connected");
  client.subscribe("pytofront");
  client.subscribe("stn1/qrg");
  client.subscribe("stn2/qrg");
  client.subscribe("stn1/mode");
  client.subscribe("stn2/mode");
  client.subscribe("stn1/op");
  client.subscribe("stn2/op");
  client.subscribe("tw1/deg");
  client.subscribe("tw2/deg");
  message = new Paho.MQTT.Message('0');
  message.destinationName = "update";
  client.send(message);
}

function onConnectionLost(responseObject) {
  if (responseObject.errorCode !== 0) {
    console.log("onConnectionLost:"+responseObject.errorMessage);
  }
}

function send_command(comm, dato){
  message = new Paho.MQTT.Message(String(dato));
  message.destinationName = comm;
  client.send(message);
}

function onMessageArrived(message) {
    console.log(message.payloadString)
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
        $('#tw1').text(message.payloadString+"º")
    } else if (message.destinationName == "tw2/deg") {
        $('#tw2').text(message.payloadString+"º")
    } else {
        json = JSON.parse(message.payloadString)
        if (json.stn1 != undefined) {
            json = JSON.parse(message.payloadString)
            bstn1 = "#stn1-b"+json.stn1.band
            bstn2 = "#stn2-b"+json.stn2.band

            bandstn1 = json.stn1.band

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

            $("#stn1-b0").removeClass("spanitemselected");
            $("#stn1-b160").removeClass("spanitemselected");
            $("#stn1-b80").removeClass("spanitemselected");
            $("#stn1-b40").removeClass("spanitemselected");
            $("#stn1-b20").removeClass("spanitemselected");
            $("#stn1-b15").removeClass("spanitemselected");
            $("#stn1-b10").removeClass("spanitemselected");
            $("#stn2-b0").removeClass("spanitemselected");

            $("#stn2-b160").removeClass("spanitemselected");
            $("#stn2-b80").removeClass("spanitemselected");
            $("#stn2-b40").removeClass("spanitemselected");
            $("#stn2-b20").removeClass("spanitemselected");
            $("#stn2-b15").removeClass("spanitemselected");
            $("#stn2-b10").removeClass("spanitemselected");

            $("#rx100").removeClass("spanitemselected");
            $("#rx101").removeClass("spanitemselected");
            $("#rx102").removeClass("spanitemselected");
            $("#rx103").removeClass("spanitemselected");
            $("#rx104").removeClass("spanitemselected");
            $("#rx105").removeClass("spanitemselected");
            $("#rx106").removeClass("spanitemselected");

            $("#rx200").removeClass("spanitemselected");
            $("#rx201").removeClass("spanitemselected");
            $("#rx202").removeClass("spanitemselected");
            $("#rx203").removeClass("spanitemselected");
            $("#rx204").removeClass("spanitemselected");
            $("#rx205").removeClass("spanitemselected");
            $("#rx206").removeClass("spanitemselected");

            $("#rx101").text(json.rx1[1]['nombre'])
            $("#rx102").text(json.rx1[2]['nombre'])
            $("#rx103").text(json.rx1[3]['nombre'])
            $("#rx104").text(json.rx1[4]['nombre'])
            $("#rx105").text(json.rx1[5]['nombre'])
            $("#rx106").text(json.rx1[6]['nombre'])

            $("#rx201").text(json.rx2[1]['nombre'])
            $("#rx202").text(json.rx2[2]['nombre'])
            $("#rx203").text(json.rx2[3]['nombre'])
            $("#rx204").text(json.rx2[4]['nombre'])
            $("#rx205").text(json.rx2[5]['nombre'])
            $("#rx206").text(json.rx2[6]['nombre'])


            $("#stn1-as").removeClass("spanitemselected");
            $("#stn2-as").removeClass("spanitemselected");

            $("#stn1-stack1").addClass("spanitemnd")
            $("#stn1-stack2").addClass("spanitemnd")
            $("#stn1-stack3").addClass("spanitemnd")
            $("#stn2-stack1").addClass("spanitemnd")
            $("#stn2-stack2").addClass("spanitemnd")
            $("#stn2-stack3").addClass("spanitemnd")

            $("#stn1-segmento").addClass("spanitemnd")
            $("#stn2-segmento").addClass("spanitemnd")

            $(bstn1).addClass("spanitemselected")
            $(bstn2).addClass("spanitemselected")

            if (asstn1 == true) $("#stn1-as").addClass("spanitemselected")
            if (asstn2 == true) $("#stn2-as").addClass("spanitemselected")

            $("#stn1-stack1").text(json.stacks[json.stn1.band][1]['nombre'])
            $("#stn1-stack2").text(json.stacks[json.stn1.band][2]['nombre'])
            $("#stn1-stack3").text(json.stacks[json.stn1.band][3]['nombre'])

            $("#rx10" + json.stn1.rx[json.stn1.band]).addClass("spanitemselected")
            $("#rx20" + json.stn2.rx[json.stn2.band]).addClass("spanitemselected")
            
            $('#stn1-n').text(json.stn1.netbios)
            $('#stn2-n').text(json.stn2.netbios)

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

            $("#stn2-stack1").text(json.stacks[json.stn2.band][1]['nombre'])
            $("#stn2-stack2").text(json.stacks[json.stn2.band][2]['nombre'])
            $("#stn2-stack3").text(json.stacks[json.stn2.band][3]['nombre'])
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

            if (json.stn1.segmento != 0 && json.stacks[json.stn1.band][1]['estado']) {
                $("#stn1-segmento").removeClass("spanitemnd").text(json.stn1.segmento)
            }
            if (json.stn2.segmento != 0 && json.stacks[json.stn2.band][1]['estado']) {
                $("#stn2-segmento").removeClass("spanitemnd").text(json.stn2.segmento)
            }


        }
    }



}