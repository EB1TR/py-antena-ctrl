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
	getPyToFrontState,
	onPyToFrontState,
	sendCommand
} from "../mqtt";

import type {
	PyToFrontState
} from "../mqtt";

import { getStation, Station, StationSettings } from "../station";

type BandSettings = StationSettings & { band?: number | string };

@action({ UUID: "com.eb1tr.tukudeck.band0" })
export class BandAction extends SingletonAction<BandSettings> {

	private readonly instances = new Map<string, {
		station: Station;
		band: number;
		unsubscribe: () => void;
	}>();

	private readonly band: number;
	private readonly label: string;

	constructor(band: number, label?: string) {
		super();

		this.band = band;
		this.label = label ?? String(band);
	}

	override async onWillAppear(
		ev: WillAppearEvent<BandSettings>
	): Promise<void> {
		this.instances.get(ev.action.id)?.unsubscribe();
		const instance = {
			station: getStation(ev.payload.settings),
			band: this.getBand(ev.payload.settings),
			unsubscribe: () => {}
		};
		this.instances.set(ev.action.id, instance);

		instance.unsubscribe = onPyToFrontState((state) => {
			void this.render(ev.action, instance.station, instance.band, state);
		});
		if (ev.payload.settings.band === undefined) {
			await ev.action.setSettings({ ...ev.payload.settings, band: instance.band });
		}
		await this.render(ev.action, instance.station, instance.band, getPyToFrontState());
	}

	override async onDidReceiveSettings(
		ev: DidReceiveSettingsEvent<BandSettings>
	): Promise<void> {
		const station = getStation(ev.payload.settings);
		const instance = this.instances.get(ev.action.id);
		if (instance) {
			instance.station = station;
			instance.band = this.getBand(ev.payload.settings);
		}
		await this.render(ev.action, station, this.getBand(ev.payload.settings), getPyToFrontState());
	}

	override onWillDisappear(
		ev: WillDisappearEvent<BandSettings>
	): void {
		this.instances.get(ev.action.id)?.unsubscribe();
		this.instances.delete(ev.action.id);
	}

	override async onKeyDown(
		ev: KeyDownEvent<BandSettings>
	): Promise<void> {
		const station = getStation(ev.payload.settings);
		sendCommand(`set/${station}/band`, this.getBand(ev.payload.settings));
	}

	private getBand(settings: BandSettings): number {
		if (settings.band === undefined || settings.band === "") return this.band;
		const band = Number(settings.band);
		return [0, 160, 80, 60, 40, 30, 20, 17, 15, 12, 10].includes(band) ? band : this.band;
	}

	private async render(
		actionInstance: { id: string; setImage(image: string): Promise<void> },
		station: Station,
		band: number,
		state?: PyToFrontState
	): Promise<void> {
		const currentBand = Number(state?.[station]?.band ?? -1);
		await setKeyImage(actionInstance, this.makeImage(currentBand === band, band, station));
	}

	private makeImage(active: boolean, band: number, station: Station): string {

		const color = active
			? "#31AA31"
			: "#FF3B3B";

		const background = active
			? "#0C1D0C"
			: "#1D0C0C";

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

				<text data-part="value"
					x="72"
					y="82"
					text-anchor="middle"
					font-family="Arial, sans-serif"
					font-size="34"
					font-weight="bold"
					fill="${color}"
				>${band === this.band ? this.label : band === 0 ? "N/A" : `${band}m`}</text>
				<text data-part="station" x="72" y="126" text-anchor="middle" font-family="Arial, sans-serif" font-size="14" font-weight="bold" fill="#A0A0A0">${station.toUpperCase()}</text>
			</svg>
		`;

		return `data:image/svg+xml;charset=utf8,${encodeURIComponent(svg)}`;
	}
}
