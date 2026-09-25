import { setKeyImage } from "../key-display";
import {
	DidReceiveSettingsEvent,
	KeyDownEvent,
	SingletonAction,
	WillAppearEvent
} from "@elgato/streamdeck";

import {
	getRotorState,
	sendCommand
} from "../mqtt";

import type {
	RotorNumber
} from "../mqtt";

export type RotorMoveCommand =
	"park" |
	"minus5" |
	"plus5";

type RotorMoveSettings = { rotor?: number | string; direction?: string; step?: number | string };

export class RotorMoveAction extends SingletonAction<RotorMoveSettings> {

	private readonly rotor: RotorNumber;
	private readonly command: RotorMoveCommand;

	constructor(
		rotor: RotorNumber,
		command: RotorMoveCommand
	) {
		super();

		this.rotor = rotor;
		this.command = command;
	}

	override async onWillAppear(
		ev: WillAppearEvent<RotorMoveSettings>
	): Promise<void> {

		const rotor = this.getRotor(ev.payload.settings);
		// Persist the original rotor for existing keys before opening the inspector.
		if (ev.payload.settings.rotor === undefined || (this.command !== "park" && ev.payload.settings.direction === undefined)) {
			await ev.action.setSettings({ ...ev.payload.settings, rotor, ...(this.command !== "park" ? { direction: this.getDirection(ev.payload.settings), step: this.getStep(ev.payload.settings) } : {}) });
		}
		await setKeyImage(ev.action, this.makeImage(rotor, ev.payload.settings));
	}

	override async onDidReceiveSettings(
		ev: DidReceiveSettingsEvent<RotorMoveSettings>
	): Promise<void> {
		await setKeyImage(ev.action, this.makeImage(this.getRotor(ev.payload.settings), ev.payload.settings));
	}

	private getRotor(settings: RotorMoveSettings): RotorNumber {
		const rotor = Number(settings.rotor);
		return rotor === 1 || rotor === 2 || rotor === 3 ? rotor : this.rotor;
	}

	override async onKeyDown(
		ev: KeyDownEvent<RotorMoveSettings>
	): Promise<void> {

		const rotor = this.getRotor(ev.payload.settings);
		const state =
			getRotorState(rotor);

		let target: number;

		if (this.command === "park") {
			target = 275;
		} else {
			if (state.setdeg === undefined || !Number.isFinite(state.setdeg)) return;
			const sign = this.getDirection(ev.payload.settings) === "minus" ? -1 : 1;
			target = state.setdeg + sign * this.getStep(ev.payload.settings);
		}

		while (target < 0) {
			target += 360;
		}

		while (target >= 360) {
			target -= 360;
		}

		sendCommand(
			`tw${rotor}/set/deg`,
			target
		);
	}

	private getDirection(settings: RotorMoveSettings): string {
		return settings.direction === "plus" || settings.direction === "minus"
			? settings.direction : this.command === "minus5" ? "minus" : "plus";
	}

	private getStep(settings: RotorMoveSettings): number {
		const step = Number(settings.step);
		return Number.isFinite(step) && step > 0 && step <= 359 ? Math.max(1, Math.round(step)) : 5;
	}

	private makeImage(rotor: RotorNumber, settings: RotorMoveSettings): string {

		let label: string;
		let detail: string;

		switch (this.command) {

			case "park":
				label = "PARK";
				detail = "275°";
				break;

			case "minus5":
				label = `${this.getDirection(settings) === "minus" ? "−" : "+"}${this.getStep(settings)}°`;
				detail = "";
				break;

			case "plus5":
				label = `${this.getDirection(settings) === "minus" ? "−" : "+"}${this.getStep(settings)}°`;
				detail = "";
				break;
		}

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
					font-size="18"
					font-weight="bold"
					fill="#006CFF"
				>TW${rotor}</text>

				<text data-part="value"
					x="72"
					y="${detail ? 75 : 86}"
					text-anchor="middle"
					font-family="Arial, sans-serif"
					font-size="30"
					font-weight="bold"
					fill="#006CFF"
				>${label}</text>

				${
					detail
						? `
							<text data-part="value"
								x="72"
								y="108"
								text-anchor="middle"
								font-family="Arial, sans-serif"
								font-size="18"
								font-weight="bold"
								fill="#A0A0A0"
							>${detail}</text>
						`
						: ""
				}
			</svg>
		`;

		return `data:image/svg+xml;charset=utf8,${encodeURIComponent(svg)}`;
	}
}
