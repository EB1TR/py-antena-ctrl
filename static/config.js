// Create a client instance
clientID = "web"
clientID += new Date().getUTCMilliseconds()
client = new Paho.MQTT.Client("127.0.0.1", Number(9001), clientID);

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
  $('input[name="a1601"]').val(json.stacks[160][1]['nombre'])
  $('input[name="a1602"]').val(json.stacks[160][2]['nombre'])
  $('input[name="a1603"]').val(json.stacks[160][3]['nombre'])
  
  $('input[name="a800"]').val(json.stacks[80]['salidas'])
  $('input[name="a801"]').val(json.stacks[80][1]['nombre'])
  $('input[name="a802"]').val(json.stacks[80][2]['nombre'])
  $('input[name="a803"]').val(json.stacks[80][3]['nombre'])
  
  $('input[name="a400"]').val(json.stacks[40]['salidas'])
  $('input[name="a401"]').val(json.stacks[40][1]['nombre'])
  $('input[name="a402"]').val(json.stacks[40][2]['nombre'])
  $('input[name="a403"]').val(json.stacks[40][3]['nombre'])
  
  $('input[name="a200"]').val(json.stacks[20]['salidas'])
  $('input[name="a201"]').val(json.stacks[20][1]['nombre'])
  $('input[name="a202"]').val(json.stacks[20][2]['nombre'])
  $('input[name="a203"]').val(json.stacks[20][3]['nombre'])
  
  $('input[name="a150"]').val(json.stacks[15]['salidas'])
  $('input[name="a151"]').val(json.stacks[15][1]['nombre'])
  $('input[name="a152"]').val(json.stacks[15][2]['nombre'])
  $('input[name="a153"]').val(json.stacks[15][3]['nombre'])
  
  $('input[name="a100"]').val(json.stacks[10]['salidas'])
  $('input[name="a101"]').val(json.stacks[10][1]['nombre'])
  $('input[name="a102"]').val(json.stacks[10][2]['nombre'])
  $('input[name="a103"]').val(json.stacks[10][3]['nombre'])

  $('input[name="r101"]').val(json.rx1['1'])
  $('input[name="r102"]').val(json.rx1['2'])
  $('input[name="r103"]').val(json.rx1['3'])
  $('input[name="r104"]').val(json.rx1['4'])
  $('input[name="r105"]').val(json.rx1['5'])
  $('input[name="r106"]').val(json.rx1['6'])

  $('input[name="r201"]').val(json.rx2['1'])
  $('input[name="r202"]').val(json.rx2['2'])
  $('input[name="r203"]').val(json.rx2['3'])
  $('input[name="r204"]').val(json.rx2['4'])
  $('input[name="r205"]').val(json.rx2['5'])
  $('input[name="r206"]').val(json.rx2['6'])


}