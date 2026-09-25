import { setKeyImage } from "../key-display";
import {
	action,
	SingletonAction,
	WillAppearEvent
} from "@elgato/streamdeck";

import {
	getTw1State,
	onTw1State,
	RotorState
} from "../mqtt";

@action({ UUID: "com.eb1tr.tukudeck.test" })
export class TukuTest extends SingletonAction {

	private action?: WillAppearEvent["action"];
	private unsubscribe?: () => void;

	override async onWillAppear(ev: WillAppearEvent): Promise<void> {
		this.action = ev.action;

		this.unsubscribe?.();

		this.unsubscribe = onTw1State((state) => {
			void this.render(state);
		});

		await this.render(getTw1State());
	}

	private async render(state: RotorState): Promise<void> {
		if (!this.action) {
			return;
		}

		const rawDeg = state.deg;

		let displayDeg = "---";
		let positionColor = "#FFFFFF";

		if (rawDeg !== undefined) {
			let normalizedDeg = rawDeg;

			if (normalizedDeg > 360) {
				normalizedDeg -= 360;
				positionColor = "#FF3B3B";
			}

			displayDeg = `${Math.round(normalizedDeg)}°`;
		}

		const mode = state.mode?.toUpperCase() ?? "---";

		let modeColor = "#808080";

		if (state.mode === "rem") {
			modeColor = "#31AA31";
		} else if (state.mode === "loc") {
			modeColor = "#FF3B3B";
		}

		const movement =
			state.nec && state.nec !== "0"
				? state.nec.toUpperCase()
				: "";

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
					fill="#101010"
					stroke="#006CFF"
					stroke-width="3"
				/>

				<text data-part="title"
					x="72"
					y="30"
					text-anchor="middle"
					font-family="Arial, sans-serif"
					font-size="19"
					font-weight="bold"
					fill="#006CFF"
				>TW1</text>

				<text data-part="value"
					x="72"
					y="79"
					text-anchor="middle"
					font-family="Arial, sans-serif"
					font-size="36"
					font-weight="bold"
					fill="${positionColor}"
				>${displayDeg}</text>

				<text data-part="value"
					x="72"
					y="113"
					text-anchor="middle"
					font-family="Arial, sans-serif"
					font-size="18"
					font-weight="bold"
					fill="${modeColor}"
				>${mode}</text>

				<text data-part="value"
					x="124"
					y="128"
					text-anchor="end"
					font-family="Arial, sans-serif"
					font-size="13"
					font-weight="bold"
					fill="#FF8000"
				>${movement}</text>
			</svg>
		`;

		const image =
			`data:image/svg+xml;charset=utf8,${encodeURIComponent(svg)}`;

		await setKeyImage(this.action, image);
	}
}