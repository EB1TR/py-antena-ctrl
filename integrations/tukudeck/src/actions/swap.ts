import { setKeyImage } from "../key-display";
import {
	action,
	KeyDownEvent,
	SingletonAction,
	WillAppearEvent
} from "@elgato/streamdeck";

import {
	sendCommand
} from "../mqtt";

@action({ UUID: "com.eb1tr.tukudeck.swap" })
export class Swap extends SingletonAction {

	override async onWillAppear(
		ev: WillAppearEvent
	): Promise<void> {

		await setKeyImage(ev.action, 
			this.makeImage()
		);
	}

	override async onKeyDown(
		_ev: KeyDownEvent
	): Promise<void> {

		sendCommand(
			"set/stn2/nostack",
			1
		);
	}

	private makeImage(): string {

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
			</svg>
		`;

		return `data:image/svg+xml;charset=utf8,${encodeURIComponent(svg)}`;
	}
}
