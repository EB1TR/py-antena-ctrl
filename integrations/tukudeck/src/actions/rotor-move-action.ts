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
	sendCommand
} from "../mqtt";

import type {
	RotorNumber
} from "../mqtt";
import { getRotorColor, onRotorColorChange } from "../rotor-colors";

type RotorMoveSettings = { rotor?: number | string; direction?: string; step?: number | string };

@action({ UUID: "com.eb1tr.tukudeck.tw1plus5" })
export class RotorMoveAction extends SingletonAction<RotorMoveSettings> {
	private readonly cleanups = new Map<string, () => void>();

	override async onWillAppear(
		ev: WillAppearEvent<RotorMoveSettings>
	): Promise<void> {

		this.subscribe(ev.action, ev.payload.settings);
	}

	override async onDidReceiveSettings(
		ev: DidReceiveSettingsEvent<RotorMoveSettings>
	): Promise<void> {
		if (this.cleanups.has(ev.action.id)) this.subscribe(ev.action, ev.payload.settings);
	}

	override onWillDisappear(ev: WillDisappearEvent<RotorMoveSettings>): void {
		this.cleanups.get(ev.action.id)?.();
		this.cleanups.delete(ev.action.id);
	}

	private subscribe(
		actionInstance: { id: string; setImage(image: string): Promise<void> },
		settings: RotorMoveSettings
	): void {
		this.cleanups.get(actionInstance.id)?.();
		const rotor = this.getRotor(settings);
		const render = (): void => {
			void setKeyImage(actionInstance, this.makeImage(rotor, settings, getRotorColor(rotor)));
		};
		const offColor = onRotorColorChange((changedRotor) => {
			if (changedRotor === rotor) render();
		});
		this.cleanups.set(actionInstance.id, offColor);
		render();
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

	private makeImage(rotor: RotorNumber, settings: RotorMoveSettings, color: string): string {

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
					stroke="${color}"
					stroke-width="3"
				/>

				<text data-part="title"
					x="72"
					y="27"
					text-anchor="middle"
					font-family="Arial, sans-serif"
					font-size="18"
					font-weight="bold"
					fill="${color}"
				>TW${rotor}</text>

				<text data-part="value"
					x="72"
					y="86"
					text-anchor="middle"
					font-family="Arial, sans-serif"
					font-size="30"
					font-weight="bold"
					fill="${color}"
				>${label}</text>

			</svg>
		`;

		return `data:image/svg+xml;charset=utf8,${encodeURIComponent(svg)}`;
	}
}
