import { action } from "@elgato/streamdeck";
import { setKeyImage } from "../key-display";
import { DidReceiveSettingsEvent, KeyDownEvent, SingletonAction, WillAppearEvent, WillDisappearEvent } from "@elgato/streamdeck";
import { getPyToFrontState, onPyToFrontState, sendCommand } from "../mqtt";
import type { AntennaState, PyToFrontState } from "../mqtt";
import { getStation } from "../station";
import type { Station, StationSettings } from "../station";

type AntennaSettings = StationSettings & { antenna?: number | string };

@action({ UUID: "com.eb1tr.tukudeck.antenna1" })
export class AntennaAction extends SingletonAction<AntennaSettings> {
	private readonly subscriptions = new Map<string, () => void>();
	constructor(private readonly antennaNumber: number) { super(); }

	private getAntenna(settings: AntennaSettings): number {
		const antenna = Number(settings.antenna);
		return [1, 2, 3].includes(antenna) ? antenna : this.antennaNumber;
	}

	override async onWillAppear(ev: WillAppearEvent<AntennaSettings>): Promise<void> {
		if (ev.payload.settings.antenna === undefined) {
			await ev.action.setSettings({ ...ev.payload.settings, antenna: this.antennaNumber });
		}
		this.subscribe(ev.action, ev.payload.settings);
	}

	override onDidReceiveSettings(ev: DidReceiveSettingsEvent<AntennaSettings>): void {
		if (this.subscriptions.has(ev.action.id)) this.subscribe(ev.action, ev.payload.settings);
	}

	override onWillDisappear(ev: WillDisappearEvent<AntennaSettings>): void {
		this.subscriptions.get(ev.action.id)?.();
		this.subscriptions.delete(ev.action.id);
	}

	private subscribe(action: { id: string; setImage(image: string): Promise<void> }, settings: AntennaSettings): void {
		this.subscriptions.get(action.id)?.();
		const number = this.getAntenna(settings);
		const station = getStation(settings);
		const render = (state?: PyToFrontState): void => {
			const antenna = this.getAntennaState(number, station, state);
			void setKeyImage(action, antenna
				? this.makeAntennaImage(number, antenna.nombre ?? `ANT${number}`, antenna.estado === true, station, antenna.tw)
				: this.makeUnavailableImage());
		};
		this.subscriptions.set(action.id, onPyToFrontState(render));
		render(getPyToFrontState());
	}

	private getAntennaState(number: number, station: Station, state?: PyToFrontState): AntennaState | undefined {
		const band = state?.[station]?.band;
		if (band === undefined) return undefined;
		const stack = state?.stacks?.[String(band)];
		if (!stack || (stack.salidas ?? 0) < number) return undefined;
		return stack[String(number)] as AntennaState | undefined;
	}

	override async onKeyDown(ev: KeyDownEvent<AntennaSettings>): Promise<void> {
		const number = this.getAntenna(ev.payload.settings);
		const station = getStation(ev.payload.settings);
		if (this.getAntennaState(number, station, getPyToFrontState())) sendCommand(`set/${station}/stack`, number);
	}

	private makeUnavailableImage(): string {

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
					fill="#080808"
					stroke="#303030"
					stroke-width="3"
				/>
			</svg>
		`;

		return `data:image/svg+xml;charset=utf8,${encodeURIComponent(svg)}`;
	}

	private makeAntennaImage(
		antennaNumber: number,
		name: string,
		active: boolean,
		station: Station,
		tw?: number
	): string {

		const color = active
			? "#31AA31"
			: "#FF3B3B";

		const background = active
			? "#0C1D0C"
			: "#1D0C0C";

		const rotor =
			tw && tw > 0
				? `TW${tw}`
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
					fill="${background}"
					stroke="${color}"
					stroke-width="3"
				/>

				<text data-part="title"
					x="72"
					y="28"
					text-anchor="middle"
					font-family="Arial, sans-serif"
					font-size="15"
					font-weight="bold"
					fill="#808080"
				>ANT${antennaNumber}</text>

				<text data-part="value"
					x="72"
					y="82"
					text-anchor="middle"
					font-family="Arial, sans-serif"
					font-size="30"
					font-weight="bold"
					fill="${color}"
				>${this.escapeXml(name)}</text>

				<text data-part="value"
					x="72"
					y="112"
					text-anchor="middle"
					font-family="Arial, sans-serif"
					font-size="16"
					font-weight="bold"
					fill="#006CFF"
				>${rotor}</text>

				<text data-part="station"
					x="72"
					y="135"
					text-anchor="middle"
					font-family="Arial, sans-serif"
					font-size="13"
					font-weight="bold"
					fill="#808080"
				>${station.toUpperCase()}</text>
			</svg>
		`;

		return `data:image/svg+xml;charset=utf8,${encodeURIComponent(svg)}`;
	}

	private escapeXml(value: string): string {
		return value
			.replaceAll("&", "&amp;")
			.replaceAll("<", "&lt;")
			.replaceAll(">", "&gt;")
			.replaceAll('"', "&quot;")
			.replaceAll("'", "&apos;");
	}
}
