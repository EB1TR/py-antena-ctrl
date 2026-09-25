import streamDeck from "@elgato/streamdeck";
import mqtt, { MqttClient } from "mqtt";

import { getRadioState, onRadioState, processRadioMessage } from "./radio-state";
import type { RadioState } from "./radio-state";

import type { Station } from "./station";

const MQTT_URL = "mqtt://192.168.88.10:1883";

const TOPICS = [
	"pytofront",
	"stn1/#",
	"stn2/#",
	"tw1/#",
	"tw2/#",
	"tw3/#"
];

export type RotorMode = "rem" | "loc" | string;

export type RotorState = {
	deg?: number;
	setdeg?: number;
	nec?: string;
	mode?: RotorMode;
};

export type RotorNumber = 1 | 2 | 3;

export type AntennaState = {
	estado?: boolean;
	nombre?: string;
	rele?: string;
	tw?: number;
};

export type StackState = {
	salidas?: number;
	balun?: boolean;
	rele?: string;
	[key: string]: unknown;
};

export type StationState = {
	netbios?: string;
	auto?: boolean;
	band?: number | string;
	rig?: number | boolean;
	rele?: string;
	segmento?: number | string;
};

export type PyToFrontState = {
	stn1?: StationState;
	stn2?: StationState;
	stacks?: Record<string, StackState>;
	sixpack?: unknown;
	[key: string]: unknown;
};

let client: MqttClient | undefined;

export type MqttConnectionState = { connected: boolean; receivedPacket: boolean; enabled: boolean };
let connectionState: MqttConnectionState = { connected: false, receivedPacket: false, enabled: false };
let startupReady = false;
let togglingConnection = false;
let packetTimeout: ReturnType<typeof setTimeout> | undefined;
const connectionListeners = new Set<(state: MqttConnectionState) => void>();

export function onMqttConnection(listener: (state: MqttConnectionState) => void): () => void {
	connectionListeners.add(listener);
	listener({ ...connectionState });
	return () => { connectionListeners.delete(listener); };
}

function notifyConnection(): void {
	for (const listener of connectionListeners) listener({ ...connectionState });
}

function setMqttConnected(connected: boolean): void {
	if (connectionState.connected === connected) return;
	if (packetTimeout !== undefined) clearTimeout(packetTimeout);
	packetTimeout = undefined;
	connectionState = { ...connectionState, connected, receivedPacket: false };
	notifyConnection();
}

function markPacketReceived(): void {
	if (!connectionState.connected) return;
	if (packetTimeout !== undefined) clearTimeout(packetTimeout);
	if (!connectionState.receivedPacket) {
		connectionState.receivedPacket = true;
		notifyConnection();
	}
	packetTimeout = setTimeout(() => {
		packetTimeout = undefined;
		connectionState.receivedPacket = false;
		notifyConnection();
	}, 5000);
}



export type TelemetryMetric = "tensiona" | "fun" | "temp" | "pwr" | "swr" | "qrg";
export type TelemetryState = Partial<Record<TelemetryMetric, number>>;

function toTelemetryState(state: RadioState): TelemetryState {
	return {
		qrg: state.frequencyKhz === null || state.frequencyKhz === 0 ? undefined : state.frequencyKhz * 100,
		pwr: state.powerWatts ?? undefined,
		swr: state.swr ?? undefined,
		tensiona: state.voltage ?? undefined,
		temp: state.temperatureCelsius ?? undefined,
		fun: state.fanRpm ?? undefined
	};
}

export function getTelemetryState(station: Station): TelemetryState {
	return toTelemetryState(getRadioState(station));
}

export function onTelemetryState(
	station: Station,
	listener: (state: TelemetryState, metric?: TelemetryMetric) => void
): () => void {
	return onRadioState(station, (state, field) => {
		if (field === undefined || ["qrg", "pwr", "swr", "tensiona", "temp", "fun"].includes(field)) {
			listener(toTelemetryState(state), field as TelemetryMetric | undefined);
		}
	});
}


/*
 * ROTORES
 */

const rotorStates: Record<RotorNumber, RotorState> = {
	1: {},
	2: {},
	3: {}
};

const rotorListeners: Record<
	RotorNumber,
	Set<(state: RotorState) => void>
> = {
	1: new Set(),
	2: new Set(),
	3: new Set()
};

export function getRotorState(
	rotor: RotorNumber
): RotorState {

	return {
		...rotorStates[rotor]
	};
}

export function onRotorState(
	rotor: RotorNumber,
	listener: (state: RotorState) => void
): () => void {

	rotorListeners[rotor].add(listener);

	listener(
		getRotorState(rotor)
	);

	return () => {
		rotorListeners[rotor].delete(listener);
	};
}

function notifyRotor(
	rotor: RotorNumber
): void {

	const state =
		getRotorState(rotor);

	for (
		const listener
		of rotorListeners[rotor]
	) {
		listener(state);
	}
}

function processRotorMessage(
	rotor: RotorNumber,
	topic: string,
	value: string
): void {

	const prefix =
		`tw${rotor}/`;

	const subtopic =
		topic.slice(prefix.length);

	const state =
		rotorStates[rotor];

	switch (subtopic) {

		case "deg": {

			const deg =
				Number(value);

			if (
				Number.isFinite(deg)
			) {
				state.deg = deg;
			}

			break;
		}

		case "setdeg": {

			const setdeg =
				Number(value);

			if (
				Number.isFinite(setdeg)
			) {
				state.setdeg = setdeg;
			}

			break;
		}

		case "nec":

			state.nec = value;

			break;

		case "mode":

			state.mode =
				value.toLowerCase();

			break;

		default:

			return;
	}

	notifyRotor(rotor);
}


/*
 * Compatibilidad temporal con tuku-test.ts
 */

export function getTw1State():
	RotorState {

	return getRotorState(1);
}

export function onTw1State(
	listener: (state: RotorState) => void
): () => void {

	return onRotorState(
		1,
		listener
	);
}


/*
 * PYTOFRONT
 */

let pyToFrontState:
	PyToFrontState | undefined;

const pyToFrontListeners =
	new Set<
		(state: PyToFrontState) => void
	>();

export function getPyToFrontState():
	PyToFrontState | undefined {

	return pyToFrontState;
}

export function onPyToFrontState(
	listener: (state: PyToFrontState) => void
): () => void {

	pyToFrontListeners.add(
		listener
	);

	if (pyToFrontState) {
		listener(
			pyToFrontState
		);
	}

	return () => {
		pyToFrontListeners.delete(
			listener
		);
	};
}

function notifyPyToFront():
	void {

	if (!pyToFrontState) {
		return;
	}

	for (
		const listener
		of pyToFrontListeners
	) {
		listener(
			pyToFrontState
		);
	}
}

function processPyToFront(
	value: string
): void {

	try {

		const data =
			JSON.parse(
				value
			) as PyToFrontState;

		pyToFrontState = data;

		streamDeck.logger.info(
			`MQTT pytofront: ` +
			`STN1 band=${data.stn1?.band} auto=${data.stn1?.auto} rig=${data.stn1?.rig} | ` +
			`STN2 band=${data.stn2?.band} auto=${data.stn2?.auto} rig=${data.stn2?.rig}`
		);

		const band =
			data.stn2?.band;

		if (
			band !== undefined &&
			data.stacks
		) {

			const stack =
				data.stacks[
					String(band)
				];

			if (stack) {

				const ant1 =
					stack["1"] as
						AntennaState | undefined;

				const ant2 =
					stack["2"] as
						AntennaState | undefined;

				const ant3 =
					stack["3"] as
						AntennaState | undefined;

				streamDeck.logger.info(
					`STN2 stack ${band}: ` +
					`salidas=${stack.salidas} | ` +
					`ANT1=${ant1?.nombre} estado=${ant1?.estado} tw=${ant1?.tw} | ` +
					`ANT2=${ant2?.nombre} estado=${ant2?.estado} tw=${ant2?.tw} | ` +
					`ANT3=${ant3?.nombre} estado=${ant3?.estado} tw=${ant3?.tw}`
				);
			}
		}

		notifyPyToFront();

	} catch (error) {

		streamDeck.logger.error(
			`MQTT: pytofront no contiene JSON válido: ${String(error)}`
		);
	}
}


/*
 * ENVÍO DE ÓRDENES
 */

export function sendCommand(
	topic: string,
	value: string | number
): void {

	if (
		!client?.connected
	) {

		streamDeck.logger.warn(
			`MQTT: no se puede enviar ${topic}=${value}: broker desconectado`
		);

		return;
	}

	const payload =
		String(value);

	client.publish(
		topic,
		payload,
		(error) => {

			if (error) {

				streamDeck.logger.error(
					`MQTT: error enviando ${topic}=${payload}: ${error.message}`
				);

				return;
			}

			streamDeck.logger.info(
				`MQTT TX: ${topic} = ${payload}`
			);
		}
	);
}


/*
 * CONEXIÓN MQTT
 */

export function initializeMqtt(connectOnStartup: boolean): void {
	if (startupReady) return;
	startupReady = true;
	if (connectOnStartup) connectMqtt();
	else notifyConnection();
}

export async function toggleMqtt(): Promise<void> {
	if (!startupReady || togglingConnection) return;
	togglingConnection = true;
	try {
		if (connectionState.enabled) {
			const previousClient = client;
			client = undefined;
			if (packetTimeout !== undefined) clearTimeout(packetTimeout);
			packetTimeout = undefined;
			connectionState = { connected: false, receivedPacket: false, enabled: false };
			notifyConnection();
			// Forced close also cancels reconnect attempts and pending MQTT traffic.
			await previousClient?.endAsync(true);
			streamDeck.logger.info("MQTT: desconectado manualmente");
		} else {
			connectMqtt();
		}
	} finally {
		togglingConnection = false;
	}
}

export function connectMqtt():
	void {

	if (client) {
		return;
	}

	connectionState = { connected: false, receivedPacket: false, enabled: true };
	notifyConnection();
	streamDeck.logger.info(
		`MQTT: conectando a ${MQTT_URL}`
	);

	client = mqtt.connect(
		MQTT_URL,
		{
			clientId:
				`tukudeck-${Date.now()}`,

			reconnectPeriod:
				5000,

			connectTimeout:
				10000,

			// Detect silent network loss without waiting for the 60 s default.
			keepalive: 5,
			reschedulePings: false
		}
	);

	const activeClient = client;

	activeClient.on(
		"connect",
		() => {
			if (client !== activeClient) return;
			setMqttConnected(true);

			streamDeck.logger.info(
				"MQTT: conectado"
			);

			activeClient.subscribe(
				TOPICS,
				(error) => {
			if (client !== activeClient) return;

					if (error) {

						streamDeck.logger.error(
							`MQTT: error al suscribirse: ${error.message}`
						);

						return;
					}

					streamDeck.logger.info(
						`MQTT: suscrito a ${TOPICS.join(", ")}`
					);
				}
			);
		}
	);

	activeClient.on(
		"message",
		(topic, payload) => {
			if (client !== activeClient) return;
			markPacketReceived();

			const value =
				payload.toString();

			processRadioMessage(topic, value);

			const match =
				topic.match(
					/^tw([123])\//
				);

			if (match) {

				const rotor =
					Number(
						match[1]
					) as RotorNumber;

				processRotorMessage(
					rotor,
					topic,
					value
				);
			}

			if (
				topic ===
				"pytofront"
			) {

				processPyToFront(
					value
				);

				return;
			}

			streamDeck.logger.info(
				`MQTT ${topic} = ${value}`
			);
		}
	);

	activeClient.on(
		"reconnect",
		() => {
			if (client !== activeClient) return;
			setMqttConnected(false);

			streamDeck.logger.info(
				"MQTT: reconectando..."
			);
		}
	);

	activeClient.on(
		"close",
		() => {
			if (client !== activeClient) return;
			setMqttConnected(false);

			streamDeck.logger.info(
				"MQTT: conexión cerrada"
			);
		}
	);

	activeClient.on(
		"offline",
		() => {
			if (client !== activeClient) return;
			setMqttConnected(false);

			streamDeck.logger.warn(
				"MQTT: broker offline"
			);
		}
	);

	activeClient.on(
		"error",
		(error) => {
			if (client !== activeClient) return;

			streamDeck.logger.error(
				`MQTT: ${error.message}`
			);
		}
	);
}
