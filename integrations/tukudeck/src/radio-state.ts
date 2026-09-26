import streamDeck from "@elgato/streamdeck";
import type { Station } from "./station";

export type RadioState = {
	available: boolean | null;
	transmitting: boolean | null;
	frequencyKhz: number | null;
	band: number | null;
	segment: number | null;
	powerWatts: number | null;
	swr: number | null;
	voltage: number | null;
	temperatureCelsius: number | null;
	fanRpm: number | null;
};
export type RadioField = "available" | "tx" | "qrg" | "band" | "pwr" | "swr" | "tensiona" | "temp" | "fun";
const emptyState = (): RadioState => ({
	available: null, transmitting: null, frequencyKhz: null, band: null,
	segment: null, powerWatts: null, swr: null, voltage: null,
	temperatureCelsius: null, fanRpm: null
});
const states: Record<Station, RadioState> = { stn1: emptyState(), stn2: emptyState() };
const listeners: Record<Station, Set<(state: RadioState, field?: RadioField) => void>> = {
	stn1: new Set(), stn2: new Set()
};
const numericFields = {
	qrg: "frequencyKhz", pwr: "powerWatts", swr: "swr", tensiona: "voltage",
	temp: "temperatureCelsius", fun: "fanRpm"
} as const;
const TELEMETRY_TIMEOUT_MS = 5000;
type TimedRadioField = keyof typeof numericFields | "band";
const telemetryTimeouts: Record<Station, Partial<Record<TimedRadioField, ReturnType<typeof setTimeout>>>> = {
	stn1: {}, stn2: {}
};

function notifyRadioState(station: Station, field: RadioField): void {
	for (const listener of listeners[station]) listener(getRadioState(station), field);
}

function clearTimedField(station: Station, field: TimedRadioField): void {
	const state = states[station];
	if (field === "band") {
		state.band = null;
		state.segment = null;
	} else {
		state[numericFields[field]] = null;
	}
	notifyRadioState(station, field);
}

function refreshTelemetryTimeout(station: Station, field: TimedRadioField): void {
	const current = telemetryTimeouts[station][field];
	if (current !== undefined) clearTimeout(current);
	telemetryTimeouts[station][field] = setTimeout(() => {
		delete telemetryTimeouts[station][field];
		clearTimedField(station, field);
	}, TELEMETRY_TIMEOUT_MS);
}

export function getRadioState(station: Station): RadioState {
	return { ...states[station] };
}

export function onRadioState(station: Station, listener: (state: RadioState, field?: RadioField) => void): () => void {
	listeners[station].add(listener);
	listener(getRadioState(station));
	return () => { listeners[station].delete(listener); };
}

export function processRadioMessage(topic: string, payload: string): void {
	const [station, field, extra] = topic.split("/");
	if ((station !== "stn1" && station !== "stn2") || extra !== undefined) return;
	if (!["available", "tx", "band", ...Object.keys(numericFields)].includes(field)) return;
	const state = states[station];
	try {
		if (field === "tx" || field === "available") {
			if (payload !== "0" && payload !== "1") throw new Error("se esperaba 0 o 1");
			if (field === "tx") state.transmitting = payload === "1";
			else state.available = payload === "1";
		} else if (field === "band") {
			const value: unknown = JSON.parse(payload);
			if (!Array.isArray(value) || value.length !== 2 ||
				!value.every(item => typeof item === "number" && Number.isFinite(item) && Number.isInteger(item) && item >= 0)) {
				throw new Error("se esperaba [banda, segmento] con enteros no negativos");
			}
			const [band, segment] = value;
			state.band = band === 0 ? null : band;
			state.segment = band === 0 ? null : segment;
		} else {
			const number = Number(payload);
			if (payload.trim() === "" || !Number.isFinite(number)) throw new Error("se esperaba un número finito");
			const key = numericFields[field as keyof typeof numericFields];
			state[key] = field === "qrg" ? (number === 0 ? null : number / 100) : number;
		}
	} catch (error) {
		streamDeck.logger.warn(`MQTT ${topic}: payload inválido ${JSON.stringify(payload)}: ${String(error)}`);
		return;
	}
	if (field === "band" || Object.hasOwn(numericFields, field)) {
		refreshTelemetryTimeout(station, field as TimedRadioField);
	}
	notifyRadioState(station, field as RadioField);
}
