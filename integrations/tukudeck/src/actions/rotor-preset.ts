import { setKeyImage } from "../key-display";
import {
	action,
	DidReceiveSettingsEvent,
	KeyDownEvent,
	SingletonAction,
	WillAppearEvent,
	WillDisappearEvent
} from "@elgato/streamdeck";

import {
	sendCommand
} from "../mqtt";
import { getRotorColor, onRotorColorChange } from "../rotor-colors";

type RotorPresetSettings = {
	rotor?: string;
	degrees?: number | string;
};

@action({ UUID: "com.eb1tr.tukudeck.rotorpreset" })
export class RotorPreset extends SingletonAction<RotorPresetSettings> {
	private readonly cleanups = new Map<string, () => void>();

	override async onWillAppear(
		ev: WillAppearEvent<RotorPresetSettings>
	): Promise<void> {

		this.subscribe(ev.action, ev.payload.settings);
	}

	override async onDidReceiveSettings(
		ev: DidReceiveSettingsEvent<RotorPresetSettings>
	): Promise<void> {

		if (this.cleanups.has(ev.action.id)) this.subscribe(ev.action, ev.payload.settings);
	}

	override onWillDisappear(ev: WillDisappearEvent<RotorPresetSettings>): void {
		this.cleanups.get(ev.action.id)?.();
		this.cleanups.delete(ev.action.id);
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

	private subscribe(
		actionInstance: {
			id: string;
			setImage(image: string): Promise<void>;
		},
		settings: RotorPresetSettings
	): void {
		this.cleanups.get(actionInstance.id)?.();

		const rotor =
			this.getRotor(settings);

		const degrees =
			this.getDegrees(settings);
		const render = (): void => {
			const color = getRotorColor(rotor);

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
					font-size="36"
					font-weight="bold"
					fill="${color}"
				>${degrees}°</text>
			</svg>
		`;

			void setKeyImage(actionInstance,
				`data:image/svg+xml;charset=utf8,${encodeURIComponent(svg)}`
			);
		};
		const offColor = onRotorColorChange((changedRotor) => {
			if (changedRotor === rotor) render();
		});
		this.cleanups.set(actionInstance.id, offColor);
		render();
	}
}
