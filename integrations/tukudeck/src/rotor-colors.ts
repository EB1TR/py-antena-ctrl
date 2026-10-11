import streamDeck from "@elgato/streamdeck";

import type { RotorNumber } from "./mqtt";

export type RotorColorGlobalSettings = {
	rotor1Color?: string;
	rotor2Color?: string;
	rotor3Color?: string;
};

const DEFAULT_COLOR = "#006CFF";
const colors: Record<RotorNumber, string> = {
	1: DEFAULT_COLOR,
	2: DEFAULT_COLOR,
	3: DEFAULT_COLOR
};
const listeners = new Set<(rotor: RotorNumber) => void>();
let initialized = false;

function validColor(value: unknown): string {
	return typeof value === "string" && /^#[0-9a-f]{6}$/i.test(value)
		? value.toUpperCase()
		: DEFAULT_COLOR;
}

export function getRotorColor(rotor: RotorNumber): string {
	return colors[rotor];
}

export function applyRotorColorSettings(settings: RotorColorGlobalSettings): void {
	for (const rotor of [1, 2, 3] as const) {
		const next = validColor(settings[`rotor${rotor}Color`]);
		if (next === colors[rotor]) continue;
		colors[rotor] = next;
		for (const listener of listeners) listener(rotor);
	}
}

export function onRotorColorChange(listener: (rotor: RotorNumber) => void): () => void {
	listeners.add(listener);
	return () => { listeners.delete(listener); };
}

export function initializeRotorColors(): void {
	if (initialized) return;
	initialized = true;
	streamDeck.settings.onDidReceiveGlobalSettings<RotorColorGlobalSettings>((ev) => {
		applyRotorColorSettings(ev.settings);
	});
}
