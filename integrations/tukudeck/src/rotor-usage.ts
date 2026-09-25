import type { AntennaState, PyToFrontState, RotorNumber } from "./mqtt";
import type { Station } from "./station";

function activeRotorAntennas(
	state: PyToFrontState | undefined,
	station: Station,
	rotor: RotorNumber
): AntennaState[] {
	const band = state?.[station]?.band;
	if (band === undefined || Number(band) === 0) return [];
	const stack = state?.stacks?.[String(band)];
	if (!stack) return [];
	const antennas: AntennaState[] = [];
	for (let output = 1; output <= Math.min(3, stack.salidas ?? 0); output++) {
		const antenna = stack[String(output)] as AntennaState | undefined;
		if (antenna?.estado === true && Number(antenna.tw) === rotor) antennas.push(antenna);
	}
	return antennas;
}

export function stationUsesRotor(state: PyToFrontState | undefined, station: Station, rotor: RotorNumber): boolean {
	return activeRotorAntennas(state, station, rotor).length > 0;
}

export function getRotorAntennaNames(state: PyToFrontState | undefined, rotor: RotorNumber): string[] {
	const antennas = [...activeRotorAntennas(state, "stn1", rotor), ...activeRotorAntennas(state, "stn2", rotor)];
	return [...new Set(antennas.map(antenna => typeof antenna.nombre === "string" ? antenna.nombre.trim() : "").filter(Boolean))];
}
