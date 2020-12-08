<<<<<<< HEAD
clientID = "stn"
clientID += new Date().getUTCMilliseconds()
client = new Paho.MQTT.Client("192.168.33.200", Number(9001), clientID);
client.onConnectionLost = onConnectionLost;
client.onMessageArrived = onMessageArrived;
=======
clientID = "web"
clientID += new Date().getUTCMilliseconds()
client = new Paho.MQTT.Client("127.0.0.1", Number(9001), clientID);

client.onConnectionLost = onConnectionLost;
client.onMessageArrived = onMessageArrived;

>>>>>>> monobanda
client.connect({onSuccess:onConnect});

function onConnect() {
  console.log("Connected");
  client.subscribe("pytofront");
  client.subscribe("stn1/radio1/qrg");
  client.subscribe("stn2/radio1/qrg");
  client.subscribe("stn1/radio1/mode");
  client.subscribe("stn2/radio1/mode");
  client.subscribe("stn1/radio1/op");
  client.subscribe("stn2/radio1/op");
<<<<<<< HEAD
  client.subscribe("spots/rbn/cw");
  client.subscribe("spots/rbn/mgm");
  client.subscribe("solar/wcy");
  client.subscribe("s/1");
  client.subscribe("s/2");
  client.subscribe("spots/spider/spots");
=======
>>>>>>> monobanda
  message = new Paho.MQTT.Message('0');
  message.destinationName = "update";
  client.send(message);
}

function onConnectionLost(responseObject) {
  if (responseObject.errorCode !== 0) {
    $("#tablestn1").addClass("blink");
    $("#tablestn2").addClass("blink");
    console.log("onConnectionLost:"+responseObject.errorMessage);
  }
}

function send_command(comm, dato){
  message = new Paho.MQTT.Message(String(dato));
  message.destinationName = comm;
  client.send(message);
}

<<<<<<< HEAD
function checkBand(qrg) {
  qrg = parseFloat(qrg)
  bandcheck = 0
  if (qrg != NaN) {
    qrg = (qrg * 100)/100
    if (qrg <= 2000) bandcheck = 160
    else if (qrg <= 4000) bandcheck = 80
    else if (qrg <= 5500) bandcheck = 60
    else if (qrg <= 7300) bandcheck = 40
    else if (qrg <= 10200) bandcheck = 30
    else if (qrg <= 14350) bandcheck = 20
    else if (qrg <= 18200) bandcheck = 17
    else if (qrg <= 21450) bandcheck = 15
    else if (qrg <= 25000) bandcheck = 12
    else if (qrg <= 30000) bandcheck = 10
    else bandcheck = 6
  }
  return bandcheck
}


function isWX(rawwx, s) {
  var jsonwx = JSON.parse(rawwx)
  var tem = jsonwx.tem.toFixed(1)
  var hum = jsonwx.hum.toFixed(1)
  var pre = jsonwx.pre.toFixed(1)
  if (s == 1) {
    $("#tem").text("Temperatura: " + tem + "ºC");
    $("#hum").text("Humedad: " + hum + "%");
    $("#pre").text("Presión: " + pre + "mbar");
  } else {
    $("#etem").text("Temperatura: " + tem + "ºC");
    $("#ehum").text("Humedad: " + hum + "%");
    $("#epre").text("Presión: " + pre + "mbar");
  }
}

function isWCY(rawwcy) {
  var jsonwcy = JSON.parse(rawwcy)
  var spottime = jsonwcy.tstamp
  var ki = jsonwcy.k
  var ai = jsonwcy.a
  var ssn = jsonwcy.ssn
  var sfi = jsonwcy.sfi
  var date = new Date(spottime * 1000);
  var hours = date.getHours();
  var minutes = "0" + date.getMinutes();
  var seconds = "0" + date.getSeconds();
  var formattedTime = hours + ':' + minutes.substr(-2)
  $("#ts").text(formattedTime);
  $("#ki").text("K: " + ki);
  $("#ai").text("A: " + ai);
  $("#sfi").text("SFI: " + sfi);
  $("#ssn").text("SSN: " + ssn);
}

function isSpot(rawspot, fromrbn, rbncw) {
  var jsonspot = JSON.parse(rawspot)
  var dxcall = jsonspot.dx
  if (dxcall == "ED1B" || dxcall == "EC1A" || dxcall == "EB1TR" || dxcall == "EA1QL") {
    var spottime = jsonspot.tstamp
    var srccall = jsonspot.src
    var qrg = jsonspot.qrg.toFixed(1)
    var band = jsonspot.band
    var cmt = jsonspot.cmt
    
    var date = new Date(spottime * 1000);
    
    var hours = date.getHours();
    var minutes = "0" + date.getMinutes();
    var seconds = "0" + date.getSeconds();
    var formattedTime = hours + ':' + minutes.substr(-2)
    var bandstn1 = checkBand($("#stn1-r1-qrg").text())
    var bandstn2 = checkBand($("#stn2-r1-qrg").text())
    
    
    if (fromrbn && rbncw) {
      if (jsonspot.db > 30) var sigcolor = "dbsig4"
      //else if (jsonspot.db > 35) var sigcolor = "dbsig3"
      //else if (jsonspot.db > 25) var sigcolor = "dbsig2"
      else if (jsonspot.db > 12) var sigcolor = "dbsig1"
      else if (jsonspot.db > 0) var sigcolor = ""
      //else var sigcolor = "dbsig0"
    } else if (fromrbn && !rbncw) {
      if (jsonspot.db > 0) var sigcolor = "dbsig4"
      //else if (jsonspot.db > 0) var sigcolor = "dbsig3"
      //else if (jsonspot.db > -5) var sigcolor = "dbsig2"
      else if (jsonspot.db > -15) var sigcolor = "dbsig1"
      else if (jsonspot.db > -30) var sigcolor = ""
      //else var sigcolor = "dbsig0"
    } else {
      var sigcolor = ""
    }

    if (band == bandstn1 && fromrbn) {
      spotline = '<tr class="spotstn1rbn ' + sigcolor +'"><td width="15%" align="left">' + formattedTime
       + '</td><td width="25%" align="left">' + srccall
       + '</td><td width="25%" align="left">' + qrg
       + '</td><td align="left" width="35%">' + cmt + '</td></tr>'
      $("#tablestn1spotrbn").prepend(spotline);
      while ($(".spotstn1rbn").length > 20){
        $(".spotstn1rbn").last().remove();
      }
    }
    if (band == bandstn1 && !fromrbn) {
      spotline = '<tr class="spotstn1 ' + sigcolor +'"><td width="15%" align="left">' + formattedTime
       + '</td><td width="25%" align="left">' + srccall
       + '</td><td width="15%" align="left">' + qrg
       + '</td><td align="left">' + cmt + '</td></tr>'
      $("#tablestn1spot").prepend(spotline);
      while ($(".spotstn1").length > 10){
        $(".spotstn1").last().remove();
      }
    }
    if (band == bandstn2 && fromrbn) {
      spotline = '<tr class="spotstn2rbn ' + sigcolor +'"><td width="15%" align="left">' + formattedTime
       + '</td><td width="25%" align="left">' + srccall
       + '</td><td width="25%" align="left">' + qrg
       + '</td><td align="left" width="35%">' + cmt + '</td></tr>'
      $("#tablestn2spotrbn").prepend(spotline);
      while ($(".spotstn2rbn").length > 20){
        $(".spotstn2rbn").last().remove();
      }
    }
    if (band == bandstn2 && !fromrbn) {
      spotline = '<tr class="spotstn2 ' + sigcolor +'"><td width="15%" align="left">' + formattedTime
       + '</td><td width="25%" align="left">' + srccall
       + '</td><td width="15%" align="left">' + qrg
       + '</td><td align="left">' + cmt + '</td></tr>'
      $("#tablestn2spot").prepend(spotline);
      while ($(".spotstn2").length > 10){
        $(".spotstn2").last().remove();
      }
    }
  }
}

=======
>>>>>>> monobanda
function onMessageArrived(message) {
    if (message.destinationName == "stn1/radio1/qrg") {
        $('#stn1-r1-qrg').text((message.payloadString/100).toFixed(2))
    } else if (message.destinationName == "stn2/radio1/qrg") {
        $('#stn2-r1-qrg').text((message.payloadString/100).toFixed(2))
    } else if (message.destinationName == "stn1/radio1/mode") {
        $('#stn1-r1-mode').text(message.payloadString)
    } else if (message.destinationName == "stn2/radio1/mode") {
        $('#stn2-r1-mode').text(message.payloadString)
    } else if (message.destinationName == "stn1/radio1/op") {
        $('#stn1-op').text(message.payloadString)
    } else if (message.destinationName == "stn2/radio1/op") {
        $('#stn2-op').text(message.payloadString)
    } else if (message.destinationName == "spots/rbn/cw") {
      isSpot(message.payloadString, true, true)
    } else if (message.destinationName == "spots/rbn/mgm") {
      isSpot(message.payloadString, true, false)
    } else if (message.destinationName == "spots/spider/spots") {
      isSpot(message.payloadString, false, false)
    } else if (message.destinationName == "solar/wcy") {
      isWCY(message.payloadString)
    } else if (message.destinationName == "s/1") {
      isWX(message.payloadString, 1)
    } else if (message.destinationName == "s/2") {
      isWX(message.payloadString, 2)
    } else {
        json = JSON.parse(message.payloadString)
        if (json.stn1 != undefined) {
            json = JSON.parse(message.payloadString)
            bstn1 = "#stn1-b"+json.stn1.band
            bstn2 = "#stn2-b"+json.stn2.band

            bandstn1 = json.stn1.band

            asstn1 = json.stn1.auto
            asstn2 = json.stn2.auto
<<<<<<< HEAD
            fsstn1 = json.stn1.bpf
            fsstn2 = json.stn2.bpf
            $('#stn1-an').text(json.stn1.antname)
            $('#stn2-an').text(json.stn2.antname)
            for (i = 0; i <= 6; i++) {
              $("#stn1-a"+i).removeClass("spanitemselected");
              $("#stn1-f"+i).removeClass("spanitemselected");
              $("#stn2-a"+i).removeClass("spanitemselected");
              $("#stn2-f"+i).removeClass("spanitemselected");
            }
            for (i = 1; i <= 2; i++) {
              $("#stn"+i+"-b0").removeClass("spanitemselected");
              $("#stn"+i+"-b160").removeClass("spanitemselected");
              $("#stn"+i+"-b80").removeClass("spanitemselected");
              $("#stn"+i+"-b40").removeClass("spanitemselected");
              $("#stn"+i+"-b20").removeClass("spanitemselected");
              $("#stn"+i+"-b15").removeClass("spanitemselected");
              $("#stn"+i+"-b10").removeClass("spanitemselected");
              $("#stn"+i+"-as").removeClass("spanitemselected");
              $("#stn"+i+"-fs").removeClass("spanitemselected");
              
            }
            $(astn1).addClass("spanitemselected")
            $(astn2).addClass("spanitemselected")
            $(bstn1).addClass("spanitemselected")
            $(bstn2).addClass("spanitemselected")
            $(fstn1).addClass("spanitemselected")
            $(fstn2).addClass("spanitemselected")
            if (asstn1 == true) $("#stn1-as").addClass("spanitemselected")
            if (asstn2 == true) $("#stn2-as").addClass("spanitemselected")
            if (fsstn1 == true) $("#stn1-fs").addClass("spanitemselected")
            if (fsstn2 == true) $("#stn2-fs").addClass("spanitemselected")
=======

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

            $("#rx101").text(json.rx1[1])
            $("#rx102").text(json.rx1[2])
            $("#rx103").text(json.rx1[3])
            $("#rx104").text(json.rx1[4])
            $("#rx105").text(json.rx1[5])
            $("#rx106").text(json.rx1[6])

            $("#rx201").text(json.rx2[1])
            $("#rx202").text(json.rx2[2])
            $("#rx203").text(json.rx2[3])
            $("#rx204").text(json.rx2[4])
            $("#rx205").text(json.rx2[5])
            $("#rx206").text(json.rx2[6])


            $("#stn1-as").removeClass("spanitemselected");
            $("#stn2-as").removeClass("spanitemselected");

            $("#stn1-stack1").addClass("spanitemnd")
            $("#stn1-stack2").addClass("spanitemnd")
            $("#stn1-stack3").addClass("spanitemnd")
            $("#stn2-stack1").addClass("spanitemnd")
            $("#stn2-stack2").addClass("spanitemnd")
            $("#stn2-stack3").addClass("spanitemnd")

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
>>>>>>> monobanda
        }
    }
}


var wcyAPI = "https://api.ure.es/v1/dk0wcy/";
function dataWCY() {
  $.ajax({
    type: "GET",
    dataType: "json",
    url: wcyAPI
  })
  .done(function(data) {
    const spottime = Math.round(Date.now() / 1000)
    var date = new Date(spottime * 1000);
    var hours = date.getHours();
    var minutes = "0" + date.getMinutes();
    var seconds = "0" + date.getSeconds();
    var formattedTime = hours + ':' + minutes.substr(-2)
    $("#ts").text(formattedTime);
    $("#ki").text("K: " + data.gmf.k3h);
    $("#ai").text("A: " + data.index.aboulder);
    $("#sfi").text("SFI: " + data.index.sfi);
    $("#ssn").text("SSN: " + data.index.ssn);
  })
}
