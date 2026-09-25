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
	getPyToFrontState,
	onPyToFrontState,
	sendCommand
} from "../mqtt";

import type {
	PyToFrontState
} from "../mqtt";

import { getStation, Station, StationSettings } from "../station";

@action({ UUID: "com.eb1tr.tukudeck.bandauto" })
export class BandAuto extends SingletonAction<StationSettings> {
	private readonly instances = new Map<string, {
		station: Station;
		unsubscribe: () => void;
	}>();

	override async onWillAppear(ev: WillAppearEvent<StationSettings>): Promise<void> {
		this.instances.get(ev.action.id)?.unsubscribe();
		const instance = {
			station: getStation(ev.payload.settings),
			unsubscribe: () => {}
		};
		this.instances.set(ev.action.id, instance);
		instance.unsubscribe = onPyToFrontState((state) => {
			void this.render(ev.action, instance.station, state);
		});
		await this.render(ev.action, instance.station, getPyToFrontState());
	}

	override async onDidReceiveSettings(ev: DidReceiveSettingsEvent<StationSettings>): Promise<void> {
		const station = getStation(ev.payload.settings);
		const instance = this.instances.get(ev.action.id);
		if (instance) instance.station = station;
		await this.render(ev.action, station, getPyToFrontState());
	}

	override onWillDisappear(ev: WillDisappearEvent<StationSettings>): void {
		this.instances.get(ev.action.id)?.unsubscribe();
		this.instances.delete(ev.action.id);
	}

	override async onKeyDown(ev: KeyDownEvent<StationSettings>): Promise<void> {
		sendCommand(`set/${getStation(ev.payload.settings)}/antm`, 0);
	}

	private async render(
		actionInstance: { id: string; setImage(image: string): Promise<void> },
		station: Station,
		state?: PyToFrontState
	): Promise<void> {
		const auto = state?.[station]?.auto;
		await setKeyImage(actionInstance, this.makeImage(auto === true, station), auto === false);
	}

	private makeImage(active: boolean, station: Station): string {

		const color = active
			? "#31AA31"
			: "#FF8000";

		const background = active
			? "#0C1D0C"
			: "#1D1208";

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
					fill="${background}"
					stroke="${color}"
					stroke-width="3"
				/>

				<text data-part="title"
					x="72"
					y="82"
					text-anchor="middle"
					font-family="Arial, sans-serif"
					font-size="30"
					font-weight="bold"
					fill="${color}"
				>AUTO</text>
				<text data-part="station" x="72" y="126" text-anchor="middle" font-family="Arial, sans-serif" font-size="14" font-weight="bold" fill="#A0A0A0">${station.toUpperCase()}</text>
			</svg>
		`;

		return `data:image/svg+xml;charset=utf8,${encodeURIComponent(svg)}`;
	}
}
