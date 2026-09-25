import { action } from "@elgato/streamdeck";
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

type RotorMoveSettings = { rotor?: number | string; direction?: string; step?: number | string };

@action({ UUID: "com.eb1tr.tukudeck.tw1plus5" })
export class RotorMoveAction extends SingletonAction<RotorMoveSettings> {

	override async onWillAppear(
		ev: WillAppearEvent<RotorMoveSettings>
	): Promise<void> {

		const rotor = this.getRotor(ev.payload.settings);
		await setKeyImage(ev.action, this.makeImage(rotor, ev.payload.settings));
	}

	override async onDidReceiveSettings(
		ev: DidReceiveSettingsEvent<RotorMoveSettings>
	): Promise<void> {
		await setKeyImage(ev.action, this.makeImage(this.getRotor(ev.payload.settings), ev.payload.settings));
	}

	private getRotor(settings: RotorMoveSettings): RotorNumber {
		const rotor = Number(settings.rotor);
		return rotor === 1 || rotor === 2 || rotor === 3 ? rotor : 1;
	}

	override async onKeyDown(
		ev: KeyDownEvent<RotorMoveSettings>
	): Promise<void> {

		const rotor = this.getRotor(ev.payload.settings);
		const state =
			getRotorState(rotor);

		if (state.setdeg === undefined || !Number.isFinite(state.setdeg)) return;
		const sign = this.getDirection(ev.payload.settings) === "minus" ? -1 : 1;
		const target = ((state.setdeg + sign * this.getStep(ev.payload.settings)) % 360 + 360) % 360;

		sendCommand(
			`tw${rotor}/set/deg`,
			target
		);
	}

	private getDirection(settings: RotorMoveSettings): string {
		return settings.direction === "plus" || settings.direction === "minus"
			? settings.direction : "plus";
	}

	private getStep(settings: RotorMoveSettings): number {
		const step = Number(settings.step);
		return Number.isFinite(step) && step > 0 && step <= 359 ? Math.max(1, Math.round(step)) : 5;
	}

	private makeImage(rotor: RotorNumber, settings: RotorMoveSettings): string {

		const label = `${this.getDirection(settings) === "minus" ? "−" : "+"}${this.getStep(settings)}°`;

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
					y="86"
					text-anchor="middle"
					font-family="Arial, sans-serif"
					font-size="30"
					font-weight="bold"
					fill="#006CFF"
				>${label}</text>

			</svg>
		`;

		return `data:image/svg+xml;charset=utf8,${encodeURIComponent(svg)}`;
	}
}
