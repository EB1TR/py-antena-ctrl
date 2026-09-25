import { setKeyImage } from "../key-display";
import {
	action,
	DidReceiveSettingsEvent,
	KeyDownEvent,
	SingletonAction,
	WillAppearEvent
} from "@elgato/streamdeck";

import {
	sendCommand
} from "../mqtt";

type RotorPresetSettings = {
	rotor?: string;
	degrees?: number | string;
};

@action({ UUID: "com.eb1tr.tukudeck.rotorpreset" })
export class RotorPreset extends SingletonAction<RotorPresetSettings> {

	override async onWillAppear(
		ev: WillAppearEvent<RotorPresetSettings>
	): Promise<void> {

		await this.render(
			ev.action,
			ev.payload.settings
		);
	}

	override async onDidReceiveSettings(
		ev: DidReceiveSettingsEvent<RotorPresetSettings>
	): Promise<void> {

		await this.render(
			ev.action,
			ev.payload.settings
		);
	}

	override async onKeyDown(
		ev: KeyDownEvent<RotorPresetSettings>
	): Promise<void> {

		const rotor =
			this.getRotor(ev.payload.settings);

		const degrees =
			this.getDegrees(ev.payload.settings);

		sendCommand(
			`tw${rotor}/set/deg`,
			degrees
		);
	}

	private getRotor(
		settings: RotorPresetSettings
	): 1 | 2 | 3 {

		const rotor =
			Number(settings.rotor ?? 1);

		if (
			rotor === 2 ||
			rotor === 3
		) {
			return rotor;
		}

		return 1;
	}

	private getDegrees(
		settings: RotorPresetSettings
	): number {

		const value =
			Number(String(settings.degrees ?? "").trim() || 270);

		if (!Number.isFinite(value)) {
			return 270;
		}

		return Math.max(
			0,
			Math.min(
				359,
				Math.round(value)
			)
		);
	}

	private async render(
		actionInstance: {
			id: string;
			setImage(image: string): Promise<void>;
		},
		settings: RotorPresetSettings
	): Promise<void> {

		const rotor =
			this.getRotor(settings);

		const degrees =
			this.getDegrees(settings);

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
					font-size="36"
					font-weight="bold"
					fill="#006CFF"
				>${degrees}°</text>
			</svg>
		`;

		await setKeyImage(actionInstance, 
			`data:image/svg+xml;charset=utf8,${encodeURIComponent(svg)}`
		);
	}
}
