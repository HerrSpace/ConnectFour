var memberDiv = "#jsGame";
var websocket = 'ws://{{host}}:{{port}}/ws';
var session   = '{{sid}}';

var players = [];


function fieldClick(col, row) {
	send_click(col, row);
}

var ws;
if (window.WebSocket) {
	ws = new WebSocket(websocket);
}
else if (window.MozWebSocket) {
	ws = MozWebSocket(websocket);
}
else {
	console.log('WebSocket Not Supported');
	//return; // TODO hide game, show error
}

window.onbeforeunload = function(e) {
	send_quit();
	ws.close(1000, 'Closed Window');

	if(!e) e = window.event;
	e.stopPropagation();
	e.preventDefault();
};

ws.onopen = function() {
	send_join();
};

//	ws.onclose = function(evt) {
//	};

ws.onmessage = function (evt) {
	var messages = evt.data;
	console.log("Received message: " + messages);
	messages = JSON.parse(messages)

	// TODO: Add json scheme checking

	for(var i=0;i<messages.length;i++){
		var user_id = messages[i]["regarding"];
		var command = messages[i]["command"];
		var payload = messages[i]["payload"];
		crunchMessage(user_id, command, payload);
	}
};

// A valid message looks like this:
// message = '[	{ "command":"join",		"payload":"",		"regarding":"c8e3f37a-b452-4c61-a3ed-4b0930fa3eb2" },
// 				{ "command":"ready",	"payload":"true",	"regarding":"c8e3f37a-b452-4c61-a3ed-4b0930fa3eb2" } ]'
function crunchMessage (user_id, command, payload) {

	console.log("Crunching: regarding="+ user_id + ", command=" + command + ", payload="+payload);

	var message_mapper = {
		'join'	: received_join,
		'quit'	: received_quit,
		'map'	: received_map,
		'won'	: received_won
	};

	if (!(command in message_mapper)){
		console.log("Unknown Command.");
		return;
	}
	message_mapper[command](user_id, payload);
}


function glow(user, field_list){
	for(var idx=0; idx < field_list.length; idx++){
		box = $("#"+field_list[idx][0]+"_"+field_list[idx][1])[0];
		box.classList.add("glow");
	}
}

function received_won(user, payload){
	glow(user, payload);
}

function received_join(user, payload){
	console.log("received join: " + user );
	players.push(user);
}

function received_quit(user, payload){
	console.log("received quit: " + user );
	// Kill Game
}

function received_map(user, payload) {
	console.log("received map: " + payload );
	for(var idY=0; idY < payload.length; idY++){
		for(var idX=0; idX < payload[idY].length; idX++){
			if		(payload[idY][idX] == players[0]) { colorField(idX, idY, "orangered"); }
			else if (payload[idY][idX] == players[1]) { colorField(idX, idY, "periwinkle"); }
			else									  { colorField(idX, idY, ""); } 
		}
	}
}

function colorField(col, row, colourClass) {
	caller = $("#"+col+"_"+row)[0];
	caller.setAttribute("class", colourClass);

//	console.log("#"+col+"_"+row+" : "+colourClass)
}

// { "command":"join",		"payload":"",		"regarding":"c8e3f37a-b452-4c61-a3ed-4b0930fa3eb2" }
// TODO: implement username in this javascript and patch it in the backend
function send_join() {
	message = [];
	message.push({
		"command": "join",
		"payload": "",
		"regarding": session
	});
	ws.send(JSON.stringify(message));
}

function send_quit() {
	message = [];
	message.push({
		"command": "quit",
		"payload": "",
		"regarding": session
	});
	ws.send(JSON.stringify(message));
}

function send_click(col, row) {
	message = [];
	message.push({
		"command": "click",
		"payload": col + "_" + row,
		"regarding": session
	});
	ws.send(JSON.stringify(message));
}	

