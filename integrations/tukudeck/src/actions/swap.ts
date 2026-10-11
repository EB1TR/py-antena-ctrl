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
import { getStation } from "../station";
import type { Station, StationSettings } from "../station";

@action({ UUID: "com.eb1tr.tukudeck.swap" })
export class Swap extends SingletonAction<StationSettings> {

	override async onWillAppear(
		ev: WillAppearEvent<StationSettings>
	): Promise<void> {

		await setKeyImage(ev.action, 
			this.makeImage(getStation(ev.payload.settings))
		);
	}

	override async onDidReceiveSettings(
		ev: DidReceiveSettingsEvent<StationSettings>
	): Promise<void> {
		await setKeyImage(ev.action, this.makeImage(getStation(ev.payload.settings)));
	}

	override async onKeyDown(
		ev: KeyDownEvent<StationSettings>
	): Promise<void> {

		sendCommand(
			`set/${getStation(ev.payload.settings)}/nostack`,
			1
		);
	}

	private makeImage(station: Station): string {

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
					fill="#1D1208"
					stroke="#FF8000"
					stroke-width="3"
				/>

				<text data-part="title"
					x="72"
					y="82"
					text-anchor="middle"
					font-family="Arial, sans-serif"
					font-size="27"
					font-weight="bold"
					fill="#FF8000"
				>SWAP</text>

				<text data-part="station"
					x="72"
					y="124"
					text-anchor="middle"
					font-family="Arial, sans-serif"
					font-size="15"
					font-weight="bold"
					fill="#808080"
				>${station.toUpperCase()}</text>
			</svg>
		`;

		return `data:image/svg+xml;charset=utf8,${encodeURIComponent(svg)}`;
	}
}
