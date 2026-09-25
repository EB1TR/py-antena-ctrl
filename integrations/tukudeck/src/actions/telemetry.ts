import { setKeyImage } from "../key-display";
import {
	action, DidReceiveSettingsEvent, SingletonAction,
	WillAppearEvent, WillDisappearEvent
} from "@elgato/streamdeck";
import { getRadioState, onRadioState } from "../radio-state";
import type { RadioState } from "../radio-state";
import { getTelemetryState, onTelemetryState } from "../mqtt";
import type { TelemetryMetric, TelemetryState } from "../mqtt";
import { getStation } from "../station";
import type { Station, StationSettings } from "../station";

type TelemetrySettings = StationSettings & { metric?: TelemetryMetric | "pwrpeak" | "tx" | "radioband"; average?: number | string };

const labels: Record<TelemetryMetric, string> = {
	tensiona: "TENSIÓN", fun: "VENT.", temp: "TEMP", pwr: "POT. MEDIA", swr: "ROE", qrg: "FREC."
};
const decimals: Record<TelemetryMetric, number> = {
	tensiona: 1, fun: 0, temp: 1, pwr: 0, swr: 1, qrg: 0
};

const units: Record<TelemetryMetric, string> = {
	tensiona: " V", fun: " RPM", temp: " ºC", pwr: " W", swr: "", qrg: " kHz"
};

@action({ UUID: "com.eb1tr.tukudeck.telemetry" })
export class Telemetry extends SingletonAction<TelemetrySettings> {
	private readonly subscriptions = new Map<string, () => void>();

	override onWillAppear(ev: WillAppearEvent<TelemetrySettings>): void {
		this.subscribe(ev.action, ev.payload.settings);
	}

	override onDidReceiveSettings(ev: DidReceiveSettingsEvent<TelemetrySettings>): void {
		// Only visible instances need a listener; onWillAppear reads saved settings.
		if (this.subscriptions.has(ev.action.id)) {
			this.subscribe(ev.action, ev.payload.settings);
		}
	}

	override onWillDisappear(ev: WillDisappearEvent<TelemetrySettings>): void {
		this.subscriptions.get(ev.action.id)?.();
		this.subscriptions.delete(ev.action.id);
	}

	private subscribe(
		actionInstance: { id: string; setImage(image: string): Promise<void> },
		settings: TelemetrySettings
	): void {
		this.subscriptions.get(actionInstance.id)?.();
		const station = getStation(settings);
		if (settings.metric === "tx" || settings.metric === "radioband") {
			const metric = settings.metric;
			let lastImage: string | undefined;
			this.subscriptions.set(actionInstance.id, onRadioState(station, (state, field) => {
				if (field !== undefined && (metric === "tx" ? field !== "tx" && field !== "available" : field !== "band")) return;
				const image = this.makeRadioImage(station, metric, state);
				if (image === lastImage) return;
				lastImage = image;
				void setKeyImage(actionInstance, image);
			}));
			return;
		}
		const peak = settings.metric === "pwrpeak";
		const metric: TelemetryMetric = peak ? "pwr" :
			settings.metric && settings.metric !== "pwrpeak" && Object.hasOwn(labels, settings.metric)
				? settings.metric : "tensiona";
		if (metric === "qrg") {
			let lastImage: string | undefined;
			this.subscriptions.set(actionInstance.id, onRadioState(station, (_state, field) => {
				if (field !== undefined && field !== "qrg" && field !== "tx") return;
				const image = this.makeImage(station, metric, getTelemetryState(station), false);
				if (image === lastImage) return;
				lastImage = image;
				void setKeyImage(actionInstance, image);
			}));
			return;
		}
		const requestedAverage = Number(settings.average ?? 1);
		const average = (metric === "pwr" || metric === "swr") &&
			[1, 5, 10, 20].includes(requestedAverage) ? requestedAverage : 1;
		const peakValues: number[] = [];
		let sum = 0;
		let count = 0;
		let lastImage: string | undefined;
		const render = (state: TelemetryState): void => {
			const image = this.makeImage(station, metric, state, peak);
			if (image !== lastImage) {
				lastImage = image;
				void setKeyImage(actionInstance, image);
			}
		};
		this.subscriptions.set(actionInstance.id, onTelemetryState(station, (state, changedMetric) => {
			if (changedMetric !== undefined && changedMetric !== metric) return;
			if (state[metric] === undefined) {
				peakValues.length = 0;
				sum = 0;
				count = 0;
				render({});
				return;
			}
			if (peak) {
				if (changedMetric !== undefined && changedMetric !== "pwr") return;
				const value = state.pwr;
				if (value !== undefined) {
					peakValues.push(value);
					if (peakValues.length > 20) peakValues.shift();
				}
				render({ pwr: peakValues.length ? Math.max(...peakValues) : undefined });
				return;
			}
			// The initial cached value is displayed but is not a new sample.
			if (changedMetric === undefined) {
				render(state);
				return;
			}
			if (changedMetric !== metric) return;
			const value = state[metric];
			if (value === undefined) return;
			sum += value;
			count++;
			if (count < average) return;
			render({ [metric]: sum / count });
			sum = 0;
			count = 0;
		}));
	}

	private makeRadioImage(station: Station, metric: "tx" | "radioband", state: RadioState): string {
		const status = state.transmitting === null ? "--" : state.transmitting ? "TX" : "RX";
		const text = metric === "radioband"
			? state.band === null ? "--" : state.band === 0 ? "N/A" : `${state.band}m`
			: status;
		const color = metric === "radioband" ? state.band === null ? "#808080" : "#31AA31"
			: state.transmitting === null ? "#808080" : state.transmitting ? "#FF3B3B" : "#31AA31";
		const svg = `<svg xmlns="http://www.w3.org/2000/svg" width="144" height="144" viewBox="0 0 144 144">
			<rect x="2" y="2" width="140" height="140" rx="12" fill="#07111D" stroke="${color}" stroke-width="3"/>
			<text data-part="${metric === "tx" ? "station" : "title"}" x="72" y="30" text-anchor="middle" font-family="Arial, sans-serif" font-size="16" font-weight="bold" fill="#808080">${metric === "tx" ? station.toUpperCase() : "BANDA RADIO"}</text>
			<text data-part="value" x="72" y="${metric === "tx" ? 92 : 78}" text-anchor="middle" font-family="Arial, sans-serif" font-size="${metric === "tx" ? 58 : 36}" font-weight="bold" fill="${color}">${text}</text>
			${metric === "radioband" ? `<text data-part="station" x="72" y="124" text-anchor="middle" font-family="Arial, sans-serif" font-size="14" font-weight="bold" fill="#808080">${station.toUpperCase()}</text>` : ""}
		</svg>`;
		return `data:image/svg+xml;charset=utf8,${encodeURIComponent(svg)}`;
	}

	private makeImage(station: Station, metric: TelemetryMetric, state: TelemetryState, peak: boolean): string {
		const value = state[metric];
		// QRG uses the same scale as the web: received value / 100 = kHz.
		const displayValue = metric === "qrg" && value !== undefined ? value / 100 : value;
		const text = displayValue === undefined ? "--" : `${displayValue.toFixed(decimals[metric])}${metric === "qrg" ? "" : units[metric]}`;
		let color = "#31AA31";
		if (value === undefined) {
			color = "#808080";
		} else if (
			(metric === "qrg" && getRadioState(station).transmitting === true) ||
			(metric === "swr" && value > 3) ||
			(metric === "pwr" && value > 90) ||
			(metric === "tensiona" && value < 12.8) ||
			(metric === "temp" && value > 40)
		) {
			color = "#FF3B3B";
		} else if (metric === "swr" && value > 2) {
			color = "#FF8000";
		}
		const fontSize = Math.min(36, Math.floor(120 / (text.length * 0.65)));
		const svg = `
			<svg xmlns="http://www.w3.org/2000/svg" width="144" height="144" viewBox="0 0 144 144">
				<rect x="2" y="2" width="140" height="140" rx="12" fill="#07111D" stroke="${color}" stroke-width="3"/>
				<text data-part="title" x="72" y="30" text-anchor="middle" font-family="Arial, sans-serif" font-size="16" font-weight="bold" fill="#808080">${peak ? "POT. PICO" : labels[metric]}</text>
				<text data-part="value" x="72" y="${metric === "qrg" ? 78 : 91}" text-anchor="middle" font-family="Arial, sans-serif" font-size="${fontSize}" font-weight="bold" fill="${color}">${text}</text>
				${metric === "qrg" ? `<text data-part="value" x="72" y="101" text-anchor="middle" font-family="Arial, sans-serif" font-size="16" fill="#808080">kHz</text>` : ""}
				<text data-part="station" x="72" y="124" text-anchor="middle" font-family="Arial, sans-serif" font-size="14" font-weight="bold" fill="#808080">${station.toUpperCase()}</text>
			</svg>`;
		return `data:image/svg+xml;charset=utf8,${encodeURIComponent(svg)}`;
	}
}
