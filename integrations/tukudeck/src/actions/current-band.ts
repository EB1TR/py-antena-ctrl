import { getRadioState, onRadioState } from "../radio-state";
import { setKeyImage } from "../key-display";
import {
	action,
	DidReceiveSettingsEvent,
	SingletonAction,
	WillAppearEvent,
	WillDisappearEvent
} from "@elgato/streamdeck";

import {
	getPyToFrontState,
	onPyToFrontState
} from "../mqtt";

import type {
	PyToFrontState
} from "../mqtt";

import { getStation, Station, StationSettings } from "../station";

@action({ UUID: "com.eb1tr.tukudeck.currentband" })
export class CurrentBand extends SingletonAction<StationSettings> {

	private readonly instances = new Map<string, {
		station: Station;
		unsubscribe: () => void;
	}>();

	override async onWillAppear(
		ev: WillAppearEvent<StationSettings>
	): Promise<void> {
		await this.subscribe(ev.action, ev.payload.settings);
	}

	private async subscribe(
		actionInstance: { id: string; setImage(image: string): Promise<void> },
		settings: StationSettings
	): Promise<void> {
		this.instances.get(actionInstance.id)?.unsubscribe();

		const instance = {
			station: getStation(settings),
			unsubscribe: () => {}
		};
		this.instances.set(actionInstance.id, instance);

		const offSystem = onPyToFrontState((state) => {
			void setKeyImage(actionInstance, this.makeImage(instance.station, state));
		});
		const offRadio = onRadioState(instance.station, (_state, field) => {
			if (field === undefined || field === "tx") {
				void setKeyImage(actionInstance, this.makeImage(instance.station, getPyToFrontState()));
			}
		});
		instance.unsubscribe = () => { offSystem(); offRadio(); };

		await setKeyImage(actionInstance, 
			this.makeImage(instance.station, getPyToFrontState())
		);
	}

	override async onDidReceiveSettings(
		ev: DidReceiveSettingsEvent<StationSettings>
	): Promise<void> {
		// Rebind both sources when this key changes station.
		await this.subscribe(ev.action, ev.payload.settings);
	}

	override onWillDisappear(
		ev: WillDisappearEvent<StationSettings>
	): void {
		this.instances.get(ev.action.id)?.unsubscribe();
		this.instances.delete(ev.action.id);
	}

	private makeImage(
		station: Station,
		state?: PyToFrontState
	): string {

		const rawBand =
			state?.[station]?.band;

		let band: string;

		if (
			rawBand === undefined ||
			rawBand === null
		) {
			band = "---";
		} else if (
			Number(rawBand) === 0
		) {
			band = "N/A";
		} else {
			band = `${rawBand}m`;
		}

		const color = getRadioState(station).transmitting === true ? "#FF3B3B" : "#31AA31";
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
					y="30"
					text-anchor="middle"
					font-family="Arial, sans-serif"
					font-size="16"
					font-weight="bold"
					fill="#808080"
				>BANDA</text>

				<text data-part="value"
					x="72"
					y="91"
					text-anchor="middle"
					font-family="Arial, sans-serif"
					font-size="40"
					font-weight="bold"
					fill="${color}"
				>${band}</text>

				<text data-part="station"
					x="72"
					y="124"
					text-anchor="middle"
					font-family="Arial, sans-serif"
					font-size="14"
					font-weight="bold"
					fill="#808080"
				>${station.toUpperCase()}</text>
			</svg>
		`;

		return `data:image/svg+xml;charset=utf8,${encodeURIComponent(svg)}`;
	}
}
