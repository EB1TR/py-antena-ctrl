export const WEATHER_TOPIC = "meteo/tuku";
export const WEATHER_TIMEOUT_MS = 5 * 60 * 1000;
export const WEATHER_METRICS = {
	temp_out_c: { label: "TEMP. EXTERIOR", unit: "°C", decimals: 1 },
	humidity_out_pct: { label: "HUMEDAD", unit: "%", decimals: 0 },
	wind_speed_kmh: { label: "VIENTO", unit: "km/h", decimals: 1 },
	wind_dir_deg: { label: "DIRECCIÓN", unit: "°", decimals: 0 },
	wind_gust_kmh: { label: "RACHA", unit: "km/h", decimals: 1 },
	max_daily_gust_kmh: { label: "RACHA MÁX. HOY", unit: "km/h", decimals: 1 },
	rain_rate_mm_h: { label: "RITMO LLUVIA", unit: "mm/h", decimals: 1 },
	daily_rain_mm: { label: "LLUVIA HOY", unit: "mm", decimals: 1 }
} as const;
export type WeatherMetric = keyof typeof WEATHER_METRICS;
export type WeatherSettings = { metrics?: string[]; interval?: number | string; color?: string };
export type WeatherState = { fields: Partial<Record<WeatherMetric, number>>; receivedAt?: number; stale: boolean };
export const DEFAULT_WEATHER_METRICS: WeatherMetric[] = ["temp_out_c", "humidity_out_pct", "wind_speed_kmh", "wind_gust_kmh", "daily_rain_mm"];
let latest: Omit<WeatherState, "stale"> = { fields: {} };
const listeners = new Set<() => void>();

export function selectedWeatherMetrics(settings: WeatherSettings): WeatherMetric[] {
	if (!Array.isArray(settings.metrics)) return [...DEFAULT_WEATHER_METRICS];
	return [...new Set(settings.metrics.filter((key): key is WeatherMetric => typeof key === "string" && Object.hasOwn(WEATHER_METRICS, key)))];
}

export function weatherInterval(settings: WeatherSettings): number {
	const seconds = Number(settings.interval ?? 5);
	return (Number.isFinite(seconds) ? Math.min(60, Math.max(1, seconds)) : 5) * 1000;
}

export function getWeatherState(now = Date.now()): WeatherState {
	const age = latest.receivedAt === undefined ? Infinity : now - latest.receivedAt;
	const stale = age < -60000 || age > WEATHER_TIMEOUT_MS;
	return { fields: stale ? {} : { ...latest.fields }, receivedAt: latest.receivedAt, stale };
}

export function processWeatherMessage(payload: string): void {
	try {
		const data = JSON.parse(payload);
		const receivedAt = typeof data?.received_at === "string" ? Date.parse(data.received_at) : NaN;
		if (!Number.isFinite(receivedAt) || !data.fields || typeof data.fields !== "object" || Array.isArray(data.fields)) throw new Error("Invalid weather packet");
		const fields: WeatherState["fields"] = {};
		for (const key of Object.keys(WEATHER_METRICS) as WeatherMetric[]) {
			const value = data.fields[key];
			if (typeof value === "number" && Number.isFinite(value)) fields[key] = value;
		}
		latest = { fields, receivedAt };
	} catch {
		latest = { fields: {} };
	}
	for (const listener of listeners) listener();
}

export function onWeatherState(listener: () => void): () => void {
	listeners.add(listener);
	listener();
	return () => { listeners.delete(listener); };
}

export function formatWeatherMetric(metric: WeatherMetric, state: WeatherState): { value: string; unit: string } {
	const definition = WEATHER_METRICS[metric], raw = state.stale ? undefined : state.fields[metric];
	if (raw === undefined) return { value: "--", unit: definition.unit };
	if (metric === "wind_dir_deg") {
		const deg = ((raw % 360) + 360) % 360;
		const cardinal = ["N", "NNE", "NE", "ENE", "E", "ESE", "SE", "SSE", "S", "SSO", "SO", "OSO", "O", "ONO", "NO", "NNO"][Math.round(deg / 22.5) % 16];
		return { value: `${Math.round(deg) % 360}°`, unit: cardinal };
	}
	return { value: raw.toFixed(definition.decimals).replace(".", ","), unit: definition.unit };
}
