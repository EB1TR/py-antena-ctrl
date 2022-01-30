// Create a client instance
clientID = "web"
clientID += new Date().getUTCMilliseconds()
client = new Paho.MQTT.Client("192.168.33.62", Number(9001), clientID);

// set callback handlers
client.onConnectionLost = onConnectionLost;
client.onMessageArrived = onMessageArrived;

// connect the client
client.connect({onSuccess:onConnect});

(function() {
	function toJSONString( form ) {
		var obj = {};
		var elements = form.querySelectorAll( "input, select, textarea" );
		for( var i = 0; i < elements.length; ++i ) {
			var element = elements[i];
			var name = element.name;
			var value = element.value;

			if( name ) {
				obj[ name ] = value;
			}
		}

		return JSON.stringify( obj );
	}

	document.addEventListener( "DOMContentLoaded", function() {
		var form = document.getElementById( "configuracion" );
		var output = document.getElementById( "output" );
		form.addEventListener( "submit", function( e ) {
			e.preventDefault();
			var json = toJSONString( this );
      send_config(json)

		}, false);

	});

})();

function onConnect() {
  console.log("Connected");
  client.subscribe("pytoconfig");
  message = new Paho.MQTT.Message('0');
  message.destinationName = "update";
  client.send(message);
}

function onConnectionLost(responseObject) {
  if (responseObject.errorCode !== 0) {
    console.log("onConnectionLost:"+responseObject.errorMessage);
  }
}

function send_config(dato){
  message = new Paho.MQTT.Message(String(dato));
  message.destinationName = "configtopy";
  client.send(message);
}

function onMessageArrived(message) {
  json = JSON.parse(message.payloadString)
  console.log(json)
  
  $('input[name="stn1-n"]').val(json.stn1['netbios'])
  $('input[name="stn2-n"]').val(json.stn2['netbios'])
  
  $('input[name="a1600"]').val(json.stacks[160]['salidas'])
  $('input[name="a1600t"]').val(json.stacks[160]['tta'])
  $('input[name="a1600r"]').val(json.stacks[160]['rele'])
  $('input[name="a1601"]').val(json.stacks[160][1]['nombre'])
  $('input[name="a1601t"]').val(json.stacks[160][1]['tta'])
  $('input[name="a1601r"]').val(json.stacks[160][1]['rele'])
  $('input[name="a1602"]').val(json.stacks[160][2]['nombre'])
  $('input[name="a1602t"]').val(json.stacks[160][2]['tta'])
  $('input[name="a1602r"]').val(json.stacks[160][2]['rele'])
  $('input[name="a1603"]').val(json.stacks[160][3]['nombre'])
  $('input[name="a1603t"]').val(json.stacks[160][3]['tta'])
  $('input[name="a1603r"]').val(json.stacks[160][3]['rele'])
  
  $('input[name="a800"]').val(json.stacks[80]['salidas'])
  $('input[name="a800t"]').val(json.stacks[80]['tta'])
  $('input[name="a800r"]').val(json.stacks[80]['rele'])
  $('input[name="a801"]').val(json.stacks[80][1]['nombre'])
  $('input[name="a801t"]').val(json.stacks[80][1]['tta'])
  $('input[name="a801r"]').val(json.stacks[80][1]['rele'])
  $('input[name="a802"]').val(json.stacks[80][2]['nombre'])
  $('input[name="a802t"]').val(json.stacks[80][2]['tta'])
  $('input[name="a802r"]').val(json.stacks[80][2]['rele'])
  $('input[name="a803"]').val(json.stacks[80][3]['nombre'])
  $('input[name="a803t"]').val(json.stacks[80][3]['tta'])
  $('input[name="a803r"]').val(json.stacks[80][3]['rele'])
  
  $('input[name="a400"]').val(json.stacks[40]['salidas'])
  $('input[name="a400t"]').val(json.stacks[40]['tta'])
  $('input[name="a400r"]').val(json.stacks[40]['rele'])
  $('input[name="a401"]').val(json.stacks[40][1]['nombre'])
  $('input[name="a401t"]').val(json.stacks[40][1]['tta'])
  $('input[name="a401r"]').val(json.stacks[40][1]['rele'])
  $('input[name="a402"]').val(json.stacks[40][2]['nombre'])
  $('input[name="a402t"]').val(json.stacks[40][2]['tta'])
  $('input[name="a402r"]').val(json.stacks[40][2]['rele'])
  $('input[name="a403"]').val(json.stacks[40][3]['nombre'])
  $('input[name="a403t"]').val(json.stacks[40][3]['tta'])
  $('input[name="a403r"]').val(json.stacks[40][3]['rele'])
  
  $('input[name="a200"]').val(json.stacks[20]['salidas'])
  $('input[name="a200t"]').val(json.stacks[20]['tta'])
  $('input[name="a200r"]').val(json.stacks[20]['rele'])
  $('input[name="a201"]').val(json.stacks[20][1]['nombre'])
  $('input[name="a201t"]').val(json.stacks[20][1]['tta'])
  $('input[name="a201r"]').val(json.stacks[20][1]['rele'])
  $('input[name="a202"]').val(json.stacks[20][2]['nombre'])
  $('input[name="a202t"]').val(json.stacks[20][2]['tta'])
  $('input[name="a202r"]').val(json.stacks[20][2]['rele'])
  $('input[name="a203"]').val(json.stacks[20][3]['nombre'])
  $('input[name="a203t"]').val(json.stacks[20][3]['tta'])
  $('input[name="a203r"]').val(json.stacks[20][3]['rele'])
  
  $('input[name="a150"]').val(json.stacks[15]['salidas'])
  $('input[name="a150t"]').val(json.stacks[15]['tta'])
  $('input[name="a150r"]').val(json.stacks[15]['rele'])
  $('input[name="a151"]').val(json.stacks[15][1]['nombre'])
  $('input[name="a151t"]').val(json.stacks[15][1]['tta'])
  $('input[name="a151r"]').val(json.stacks[15][1]['rele'])
  $('input[name="a152"]').val(json.stacks[15][2]['nombre'])
  $('input[name="a152t"]').val(json.stacks[15][2]['tta'])
  $('input[name="a152r"]').val(json.stacks[15][2]['rele'])
  $('input[name="a153"]').val(json.stacks[15][3]['nombre'])
  $('input[name="a153t"]').val(json.stacks[15][3]['tta'])
  $('input[name="a153r"]').val(json.stacks[15][3]['rele'])

  $('input[name="a100"]').val(json.stacks[10]['salidas'])
  $('input[name="a100t"]').val(json.stacks[10]['tta'])
  $('input[name="a100r"]').val(json.stacks[10]['rele'])
  $('input[name="a101"]').val(json.stacks[10][1]['nombre'])
  $('input[name="a101t"]').val(json.stacks[10][1]['tta'])
  $('input[name="a101r"]').val(json.stacks[10][1]['rele'])
  $('input[name="a102"]').val(json.stacks[10][2]['nombre'])
  $('input[name="a102t"]').val(json.stacks[10][2]['tta'])
  $('input[name="a102r"]').val(json.stacks[10][2]['rele'])
  $('input[name="a103"]').val(json.stacks[10][3]['nombre'])
  $('input[name="a103t"]').val(json.stacks[10][3]['tta'])
  $('input[name="a103r"]').val(json.stacks[10][3]['rele'])

  $('input[name="r101"]').val(json.rx1['1']['nombre'])
  $('input[name="r101t"]').val(json.rx1['1']['tta'])
  $('input[name="r101r"]').val(json.rx1['1']['rele'])
  $('input[name="r102"]').val(json.rx1['2']['nombre'])
  $('input[name="r102t"]').val(json.rx1['2']['tta'])
  $('input[name="r102r"]').val(json.rx1['2']['rele'])
  $('input[name="r103"]').val(json.rx1['3']['nombre'])
  $('input[name="r103t"]').val(json.rx1['3']['tta'])
  $('input[name="r103r"]').val(json.rx1['3']['rele'])
  $('input[name="r104"]').val(json.rx1['4']['nombre'])
  $('input[name="r104t"]').val(json.rx1['4']['tta'])
  $('input[name="r104r"]').val(json.rx1['4']['rele'])
  $('input[name="r105"]').val(json.rx1['5']['nombre'])
  $('input[name="r105t"]').val(json.rx1['5']['tta'])
  $('input[name="r105r"]').val(json.rx1['5']['rele'])
  $('input[name="r106"]').val(json.rx1['6']['nombre'])
  $('input[name="r106t"]').val(json.rx1['6']['tta'])
  $('input[name="r106r"]').val(json.rx1['6']['rele'])

  $('input[name="r201"]').val(json.rx2['1']['nombre'])
  $('input[name="r201t"]').val(json.rx2['1']['tta'])
  $('input[name="r201r"]').val(json.rx2['1']['rele'])
  $('input[name="r202"]').val(json.rx2['2']['nombre'])
  $('input[name="r202t"]').val(json.rx2['2']['tta'])
  $('input[name="r202r"]').val(json.rx2['2']['rele'])
  $('input[name="r203"]').val(json.rx2['3']['nombre'])
  $('input[name="r203t"]').val(json.rx2['3']['tta'])
  $('input[name="r203r"]').val(json.rx2['3']['rele'])
  $('input[name="r204"]').val(json.rx2['4']['nombre'])
  $('input[name="r204t"]').val(json.rx2['4']['tta'])
  $('input[name="r204r"]').val(json.rx2['4']['rele'])
  $('input[name="r205"]').val(json.rx2['5']['nombre'])
  $('input[name="r205t"]').val(json.rx2['5']['tta'])
  $('input[name="r205r"]').val(json.rx2['5']['rele'])
  $('input[name="r206"]').val(json.rx2['6']['nombre'])
  $('input[name="r206t"]').val(json.rx2['6']['tta'])
  $('input[name="r206r"]').val(json.rx2['6']['rele'])

  $('input[name="sp110t"]').val(json.sixpack['1']['10']['tta'])
  $('input[name="sp110r"]').val(json.sixpack['1']['10']['rele'])
  $('input[name="sp115t"]').val(json.sixpack['1']['15']['tta'])
  $('input[name="sp115r"]').val(json.sixpack['1']['15']['rele'])
  $('input[name="sp120t"]').val(json.sixpack['1']['20']['tta'])
  $('input[name="sp120r"]').val(json.sixpack['1']['20']['rele'])
  $('input[name="sp140t"]').val(json.sixpack['1']['40']['tta'])
  $('input[name="sp140r"]').val(json.sixpack['1']['40']['rele'])
  $('input[name="sp180t"]').val(json.sixpack['1']['80']['tta'])
  $('input[name="sp180r"]').val(json.sixpack['1']['80']['rele'])
  $('input[name="sp1160t"]').val(json.sixpack['1']['160']['tta'])
  $('input[name="sp1160r"]').val(json.sixpack['1']['160']['rele'])

  $('input[name="sp210t"]').val(json.sixpack['2']['10']['tta'])
  $('input[name="sp210r"]').val(json.sixpack['2']['10']['rele'])
  $('input[name="sp215t"]').val(json.sixpack['2']['15']['tta'])
  $('input[name="sp215r"]').val(json.sixpack['2']['15']['rele'])
  $('input[name="sp220t"]').val(json.sixpack['2']['20']['tta'])
  $('input[name="sp220r"]').val(json.sixpack['2']['20']['rele'])
  $('input[name="sp240t"]').val(json.sixpack['2']['40']['tta'])
  $('input[name="sp240r"]').val(json.sixpack['2']['40']['rele'])
  $('input[name="sp280t"]').val(json.sixpack['2']['80']['tta'])
  $('input[name="sp280r"]').val(json.sixpack['2']['80']['rele'])
  $('input[name="sp2160t"]').val(json.sixpack['2']['160']['tta'])
  $('input[name="sp2160r"]').val(json.sixpack['2']['160']['rele'])

  $('input[name="s801c"]').val(json.segmentos['80']['1']['principio'])
  $('input[name="s801f"]').val(json.segmentos['80']['1']['fin'])
  $('input[name="s801t"]').val(json.segmentos['80']['1']['tta'])
  $('input[name="s801r"]').val(json.segmentos['80']['1']['rele'])
  $('input[name="s802c"]').val(json.segmentos['80']['2']['principio'])
  $('input[name="s802f"]').val(json.segmentos['80']['2']['fin'])
  $('input[name="s802t"]').val(json.segmentos['80']['2']['tta'])
  $('input[name="s802r"]').val(json.segmentos['80']['2']['rele'])
  $('input[name="s803c"]').val(json.segmentos['80']['3']['principio'])
  $('input[name="s803f"]').val(json.segmentos['80']['3']['fin'])
  $('input[name="s803t"]').val(json.segmentos['80']['3']['tta'])
  $('input[name="s803r"]').val(json.segmentos['80']['3']['rele'])
  $('input[name="s804c"]').val(json.segmentos['80']['4']['principio'])
  $('input[name="s804f"]').val(json.segmentos['80']['4']['fin'])
  $('input[name="s804t"]').val(json.segmentos['80']['4']['tta'])
  $('input[name="s804r"]').val(json.segmentos['80']['4']['rele'])

  $('input[name="s1601c"]').val(json.segmentos['160']['1']['principio'])
  $('input[name="s1601f"]').val(json.segmentos['160']['1']['fin'])
  $('input[name="s1601t"]').val(json.segmentos['160']['1']['tta'])
  $('input[name="s1601r"]').val(json.segmentos['160']['1']['rele'])
  $('input[name="s1602c"]').val(json.segmentos['160']['2']['principio'])
  $('input[name="s1602f"]').val(json.segmentos['160']['2']['fin'])
  $('input[name="s1602t"]').val(json.segmentos['160']['2']['tta'])
  $('input[name="s1602r"]').val(json.segmentos['160']['2']['rele'])
  $('input[name="s1603c"]').val(json.segmentos['160']['3']['principio'])
  $('input[name="s1603f"]').val(json.segmentos['160']['3']['fin'])
  $('input[name="s1603t"]').val(json.segmentos['160']['3']['tta'])
  $('input[name="s1603r"]').val(json.segmentos['160']['3']['rele'])
  $('input[name="s1604c"]').val(json.segmentos['160']['4']['principio'])
  $('input[name="s1604f"]').val(json.segmentos['160']['4']['fin'])
  $('input[name="s1604t"]').val(json.segmentos['160']['4']['tta'])
  $('input[name="s1604r"]').val(json.segmentos['160']['4']['rele'])
}