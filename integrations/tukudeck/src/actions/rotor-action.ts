import { action } from "@elgato/streamdeck";
import { setKeyImage } from "../key-display";
import {
	DidReceiveSettingsEvent,
	KeyDownEvent,
	SingletonAction,
	WillAppearEvent,
	WillDisappearEvent
} from "@elgato/streamdeck";

import {
	getRotorState,
	getPyToFrontState,
	onPyToFrontState,
	onRotorState,
	sendCommand
} from "../mqtt";

import type {
	RotorNumber,
	RotorState
} from "../mqtt";

import { getRotorAntennaNames, stationUsesRotor } from "../rotor-usage";

type RotorEffect = "none" | "fade" | "blink1hz" | "blink2hz";
type RotorSettings = {
	rotor?: number | string;
	locEffect?: RotorEffect;
	movementEffect?: RotorEffect;
};

function getEffect(value: RotorEffect | undefined, fallback: RotorEffect): boolean | "fade" | "blink2hz" {
	const effect = value && ["none", "fade", "blink1hz", "blink2hz"].includes(value) ? value : fallback;
	return effect === "none" ? false : effect === "blink1hz" ? true : effect as "fade" | "blink2hz";
}

@action({ UUID: "com.eb1tr.tukudeck.tw1" })
export class RotorAction extends SingletonAction<RotorSettings> {

	private readonly rotor: RotorNumber;
	private readonly cleanups = new Map<string, () => void>();

	constructor(
		rotor: RotorNumber
	) {
		super();

		this.rotor = rotor;
	}

	override async onWillAppear(
		ev: WillAppearEvent<RotorSettings>
	): Promise<void> {
		const rotor = this.getRotor(ev.payload.settings);
		if (ev.payload.settings.rotor === undefined) {
			await ev.action.setSettings({ ...ev.payload.settings, rotor });
		}
		await this.subscribe(ev.action, rotor, ev.payload.settings);
	}

	override async onDidReceiveSettings(ev: DidReceiveSettingsEvent<RotorSettings>): Promise<void> {
		if (this.cleanups.has(ev.action.id)) {
			await this.subscribe(ev.action, this.getRotor(ev.payload.settings), ev.payload.settings);
		}
	}

	private getRotor(settings: RotorSettings): RotorNumber {
		const rotor = Number(settings.rotor);
		return rotor === 1 || rotor === 2 || rotor === 3 ? rotor : this.rotor;
	}

	private async subscribe(
		actionInstance: { id: string; setImage(image: string): Promise<void> },
		rotor: RotorNumber,
		settings: RotorSettings
	): Promise<void> {
		this.cleanups.get(actionInstance.id)?.();
		let rotorState = getRotorState(rotor);
		let usage: [boolean, boolean] = [false, false];
		let label = `TW${rotor}`;
		let blinkOn = true;
		let timer: ReturnType<typeof setInterval> | undefined;
		let lastImage: string | undefined;
		const render = async (): Promise<void> => {
			const image = this.makeImage(label, rotorState, usage, blinkOn);
			if (image === lastImage) return;
			lastImage = image;
			const moving = rotorState.nec === "CW" || rotorState.nec === "CCW";
			await setKeyImage(actionInstance, image,
				moving ? getEffect(settings.movementEffect, "blink2hz") :
					rotorState.mode?.toLowerCase() === "loc" ? getEffect(settings.locEffect, "fade") : false);
		};
		const updateUsage = (state = getPyToFrontState()): void => {
			label = getRotorAntennaNames(state, rotor).join(" / ") || `TW${rotor}`;
			usage = [
				stationUsesRotor(state, "stn1", rotor),
				stationUsesRotor(state, "stn2", rotor)
			];
			if (usage[0] && usage[1]) {
				if (timer === undefined) {
					blinkOn = true;
					timer = setInterval(() => {
						blinkOn = !blinkOn;
						void render();
					}, 500);
				}
			} else {
				if (timer !== undefined) clearInterval(timer);
				timer = undefined;
				blinkOn = true;
			}
			void render();
		};
		const offRotor = onRotorState(rotor, (state) => {
			rotorState = state;
			void render();
		});
		const offStation = onPyToFrontState(updateUsage);
		this.cleanups.set(actionInstance.id, () => {
			offRotor();
			offStation();
			if (timer !== undefined) clearInterval(timer);
		});
		updateUsage();
		await render();
	}

	override onWillDisappear(ev: WillDisappearEvent<RotorSettings>): void {
		this.cleanups.get(ev.action.id)?.();
		this.cleanups.delete(ev.action.id);
	}

	override async onKeyDown(
		ev: KeyDownEvent<RotorSettings>
	): Promise<void> {

		sendCommand(
			`tw${this.getRotor(ev.payload.settings)}/set/mode`,
			"invert"
		);
	}

	private makeImage(
		label: string,
		state: RotorState,
		usage: [boolean, boolean],
		blinkOn: boolean
	): string {
		const title = label.replace(/&/g, "&amp;").replace(/</g, "&lt;").replace(/>/g, "&gt;");
		const titleSize = Math.max(10, Math.min(18, Math.floor(190 / label.length)));
		const titleFit = label.length * titleSize * 0.7 > 124 ? 'textLength="124" lengthAdjust="spacingAndGlyphs"' : "";

		const shared = usage[0] && usage[1];
		const indicatorColor = shared ? "#FF8000" : "#31AA31";
		const indicatorOpacity = shared && !blinkOn ? 0 : 1;
		const rawDeg = state.deg;

		const overflow =
			rawDeg !== undefined &&
			rawDeg > 360;

		const deg =
			rawDeg === undefined
				? "---"
				: Math.round(
					overflow
						? rawDeg - 360
						: rawDeg
				).toString();

		const mode =
			(state.mode ?? "").toLowerCase();

		const modeText =
			mode === "rem"
				? "REM"
				: mode === "loc"
					? "LOC"
					: "---";

		const modeColor =
			mode === "rem"
				? "#31AA31"
				: mode === "loc"
					? "#FF3B3B"
					: "#808080";

		const degColor =
			overflow
				? "#FF3B3B"
				: "#FFFFFF";

		const movement =
			state.nec === "CW"
				? "CW"
				: state.nec === "CCW"
					? "CCW"
					: "";

		const movementColor =
			movement
				? "#FF8F27"
				: "#606060";

		const svg = `
			<svg
				xmlns="http://www.w3.org/2000/svg"
				width="144"
				height="144"
				viewBox="0 0 144 144"
			>
				<rect
					x="2"
					y="2"
					width="140"
					height="140"
					rx="12"
					fill="#07111D"
					stroke="#006CFF"
					stroke-width="3"
				/>

				<text data-part="title"
					x="72"
					y="27"
					text-anchor="middle"
					font-family="Arial, sans-serif"
					font-size="${titleSize}"
					${titleFit}
					font-weight="bold"
					fill="#006CFF"
				>${title}</text>


				<text data-part="value"
					x="72"
					y="72"
					text-anchor="middle"
					font-family="Arial, sans-serif"
					font-size="36"
					font-weight="bold"
					fill="${degColor}"
				>${deg}°</text>

				<g font-family="Arial, sans-serif" font-size="18" font-weight="bold" text-anchor="middle" fill="${indicatorColor}" opacity="${indicatorOpacity}">
					${usage[0] ? '<text data-part="station" x="38" y="98">STN1</text>' : ""}
					${usage[1] ? '<text data-part="station" x="106" y="98">STN2</text>' : ""}
				</g>

				<text data-part="value"
					x="38"
					y="125"
					text-anchor="middle"
					font-family="Arial, sans-serif"
					font-size="20"
					font-weight="bold"
					fill="${modeColor}"
				>${modeText}</text>

				${movement ? `
					<g data-part="value" transform="translate(105 117) scale(${movement === "CCW" ? -1 : 1} 1)" fill="none" stroke="${movementColor}" stroke-width="3" stroke-linecap="round" stroke-linejoin="round">
						<path d="M -7 8 A 11 11 0 1 1 11 0"/>
						<path d="M 6 -4 L 11 1 L 16 -4"/>
					</g>
				` : ""}
			</svg>
		`;

		return `data:image/svg+xml;charset=utf8,${encodeURIComponent(svg)}`;
	}
}
