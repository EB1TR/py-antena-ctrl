import { action, SingletonAction, type DidReceiveSettingsEvent, type KeyDownEvent, type WillAppearEvent, type WillDisappearEvent } from "@elgato/streamdeck";
import { setKeyImage } from "../key-display";
import { formatWeatherMetric, getWeatherState, onWeatherState, selectedWeatherMetrics, weatherInterval, WEATHER_METRICS, type WeatherMetric, type WeatherSettings } from "../weather-state";

type ImageAction = { id: string; setImage(image: string): Promise<void> };
type Instance = { action: ImageAction; metrics: WeatherMetric[]; index: number; nextAt: number; interval: number; color: string; lastImage?: string; timer?: ReturnType<typeof setInterval>; unsubscribe?: () => void };

@action({ UUID: "com.eb1tr.tukudeck.weather" })
export class Weather extends SingletonAction<WeatherSettings> {
	private readonly instances = new Map<string, Instance>();

	override onWillAppear(ev: WillAppearEvent<WeatherSettings>): void {
		this.start(ev.action, ev.payload.settings);
	}
	override onDidReceiveSettings(ev: DidReceiveSettingsEvent<WeatherSettings>): void {
		if (this.instances.has(ev.action.id)) this.start(ev.action, ev.payload.settings);
	}
	override onWillDisappear(ev: WillDisappearEvent<WeatherSettings>): void {
		this.stop(ev.action.id);
	}
	override onKeyDown(ev: KeyDownEvent<WeatherSettings>): void {
		const instance = this.instances.get(ev.action.id);
		if (!instance || !instance.metrics.length) return;
		instance.index = (instance.index + 1) % instance.metrics.length;
		instance.nextAt = Date.now() + instance.interval;
		this.render(instance);
	}

	private stop(id: string): void {
		const instance = this.instances.get(id);
		if (!instance) return;
		if (instance.timer !== undefined) clearInterval(instance.timer);
		instance.unsubscribe?.();
		this.instances.delete(id);
	}
	private start(actionInstance: ImageAction, settings: WeatherSettings): void {
		this.stop(actionInstance.id);
		const interval = weatherInterval(settings);
		const instance: Instance = { action: actionInstance, metrics: selectedWeatherMetrics(settings), index: 0,
			nextAt: Date.now() + interval, interval, color: typeof settings.color === "string" && /^#[0-9a-f]{6}$/i.test(settings.color) ? settings.color : "#25C6E8" };
		this.instances.set(actionInstance.id, instance);
		instance.unsubscribe = onWeatherState(() => this.render(instance));
		// Tick only visible keys; paint only changed images. Also checks retained-data age.
		instance.timer = setInterval(() => {
			const now = Date.now();
			if (instance.metrics.length > 1 && now >= instance.nextAt) {
				const steps = Math.floor((now - instance.nextAt) / interval) + 1;
				instance.index = (instance.index + steps) % instance.metrics.length;
				instance.nextAt += steps * interval;
			}
			this.render(instance);
		}, 1000);
	}
	private render(instance: Instance): void {
		const metric = instance.metrics[instance.index], state = getWeatherState();
		const { value, unit } = metric ? formatWeatherMetric(metric, state) : { value: "--", unit: "SIN SELECCIÓN" };
		const title = metric ? WEATHER_METRICS[metric].label : "METEO";
		const available = metric && !state.stale && state.fields[metric] !== undefined;
		const color = available ? instance.color : "#808080";
		const fontSize = Math.max(18, Math.min(44, Math.floor(120 / (value.length * 0.65))));
		const count = instance.metrics.length, indicator = count ? `${instance.index + 1}/${count}` : "";
		const svg = `<svg xmlns="http://www.w3.org/2000/svg" width="144" height="144" viewBox="0 0 144 144">
			<rect x="2" y="2" width="140" height="140" rx="12" fill="#07111D" stroke="${color}" stroke-width="3"/>
			<text data-part="title" x="72" y="27" text-anchor="middle" font-family="Arial,sans-serif" font-size="13" font-weight="bold" fill="#7990A1">${title}</text>
			<text data-part="value" x="72" y="80" text-anchor="middle" font-family="Arial,sans-serif" font-size="${fontSize}" font-weight="bold" fill="${color}">${value}</text>
			<text data-part="value" x="72" y="104" text-anchor="middle" font-family="Arial,sans-serif" font-size="18" fill="${color}">${unit}</text>
			<text x="72" y="129" text-anchor="middle" font-family="Arial,sans-serif" font-size="12" fill="#7990A1">${indicator}</text>
		</svg>`;
		const image = `data:image/svg+xml;charset=utf8,${encodeURIComponent(svg)}`;
		if (image === instance.lastImage) return;
		instance.lastImage = image;
		void setKeyImage(instance.action, image);
	}
}
