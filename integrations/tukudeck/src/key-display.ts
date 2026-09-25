import streamDeck from "@elgato/streamdeck";
import { onMqttConnection } from "./mqtt";

type ImageAction = { id: string; setImage(image: string): Promise<void> };
type Display = {
	action: ImageAction;
	image: string;
	effect: boolean | "fade" | "blink2hz";
	lastSent?: string;
	pending: Promise<void>;
};

const visible = new Set<string>();
const displays = new Map<string, Display>();
const displaySettings = new Map<string, Record<string, unknown>>();

// SVG elements are explicitly classified by the action that renders them.
export function applyDisplaySettings(image: string, settings: Record<string, unknown>): string {
	const prefix = "data:image/svg+xml;charset=utf8,";
	if (!image.startsWith(prefix)) return image;
	let svg = decodeURIComponent(image.slice(prefix.length));
	for (const [part, key] of [["title", "showTitle"], ["value", "showValue"], ["station", "showStation"]]) {
		if (settings[key] !== "hide" && settings[key] !== false) continue;
		svg = svg.replace(new RegExp(`<(text|tspan|g)\\b[^>]*data-part="${part}"[^>]*>[\\s\\S]*?<\\/\\1>`, "g"), "");
	}
	return prefix + encodeURIComponent(svg);
}
const blank = `data:image/svg+xml;charset=utf8,${encodeURIComponent('<svg xmlns="http://www.w3.org/2000/svg" width="144" height="144"><rect width="144" height="144" fill="#000000"/></svg>')}`;
let connected = false;
let animationStart = Date.now();
let timerPeriod: number | undefined;
let timer: ReturnType<typeof setInterval> | undefined;
let initialized = false;

function paint(display: Display): Promise<void> {
	const elapsed = Date.now() - animationStart;
	const lit = Math.floor(elapsed / 500) % 2 === 0;
	let image = applyDisplaySettings(display.image, displaySettings.get(display.action.id) ?? {});
	if (!connected || display.effect === true) {
		image = lit ? image : blank;
	} else if (display.effect === "blink2hz") {
		image = Math.floor(elapsed / 250) % 2 === 0 ? image : blank;
	} else if (display.effect === "fade") {
		// A black overlay dims the SVG without relying on SVG animation support.
		// Two-second cycle, from full brightness to 20% and back.
		const opacity = (0.4 * (1 - Math.cos(2 * Math.PI * elapsed / 2000))).toFixed(3);
		const prefix = "data:image/svg+xml;charset=utf8,";
		if (image.startsWith(prefix)) {
			const svg = decodeURIComponent(image.slice(prefix.length));
			image = prefix + encodeURIComponent(svg.replace('</svg>',
				`<rect width="144" height="144" fill="#000000" opacity="${opacity}"/></svg>`));
		}
	}
	if (image === display.lastSent) return display.pending;
	display.lastSent = image;
	display.pending = display.pending.then(async () => {
		if (displays.get(display.action.id) !== display) return;
		await display.action.setImage(image);
	}).catch((error: unknown) => {
		display.lastSent = undefined;
		streamDeck.logger.error(`Error actualizando tecla: ${String(error)}`);
	});
	return display.pending;
}

function updateTimer(): void {
	const hasFade = connected && [...displays.values()].some(display => display.effect === "fade");
	const hasFastBlink = connected && [...displays.values()].some(display => display.effect === "blink2hz");
	const hasEffect = [...displays.values()].some(display => display.effect !== false);
	const period = displays.size > 0 && (!connected || hasEffect) ? (hasFastBlink ? (hasFade ? 50 : 250) : hasFade ? 100 : 500) : undefined;
	if (period === timerPeriod) return;
	if (timer !== undefined) clearInterval(timer);
	timer = undefined;
	timerPeriod = period;
	if (period !== undefined) {
		animationStart = Date.now();
		timer = setInterval(() => {
			for (const display of displays.values()) void paint(display);
		}, period);
	}
}

export function initializeKeyDisplay(): void {
	if (initialized) return;
	initialized = true;
	// Register before action handlers so their first render is tracked.
	streamDeck.actions.onWillAppear((ev) => {
		visible.add(ev.action.id);
		displaySettings.set(ev.action.id, ev.payload.settings);
	});
	streamDeck.settings.onDidReceiveSettings((ev) => {
		if (!visible.has(ev.action.id)) return;
		displaySettings.set(ev.action.id, ev.payload.settings);
		const display = displays.get(ev.action.id);
		if (display) void paint(display);
	});
	streamDeck.actions.onWillDisappear((ev) => {
		visible.delete(ev.action.id);
		displaySettings.delete(ev.action.id);
		displays.delete(ev.action.id);
		updateTimer();
	});
	onMqttConnection((state) => {
		if (connected === state.connected) return;
		connected = state.connected;
		animationStart = Date.now();
		updateTimer();
		for (const display of displays.values()) void paint(display);
	});
}

export function setKeyImage(action: ImageAction, image: string, effect: boolean | "fade" | "blink2hz" = false): Promise<void> {
	if (!visible.has(action.id)) return Promise.resolve();
	let display = displays.get(action.id);
	if (!display) {
		display = { action, image, effect, pending: Promise.resolve() };
		displays.set(action.id, display);
	} else {
		display.action = action;
		display.image = image;
		display.effect = effect;
	}
	updateTimer();
	return paint(display);
}
