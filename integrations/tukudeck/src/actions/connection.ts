import { setKeyImage } from "../key-display";
import { action, KeyDownEvent, SingletonAction, WillAppearEvent, WillDisappearEvent } from "@elgato/streamdeck";
import { onMqttConnection, MqttConnectionState, toggleMqtt } from "../mqtt";

@action({ UUID: "com.eb1tr.tukudeck.connection" })
export class Connection extends SingletonAction {
	private readonly subscriptions = new Map<string, () => void>();

	override onWillAppear(ev: WillAppearEvent): void {
		this.subscriptions.get(ev.action.id)?.();
		this.subscriptions.set(ev.action.id, onMqttConnection((connected) => {
			void setKeyImage(ev.action, this.makeImage(connected));
		}));
	}

	override onWillDisappear(ev: WillDisappearEvent): void {
		this.subscriptions.get(ev.action.id)?.();
		this.subscriptions.delete(ev.action.id);
	}

	override async onKeyDown(_ev: KeyDownEvent): Promise<void> {
		await toggleMqtt();
	}

	private makeImage(state: MqttConnectionState): string {
		const mqttColor = state.connected ? "#31AA31" : "#FF3B3B";
		const packetColor = state.receivedPacket ? "#31AA31" : "#808080";
		const svg = `<svg xmlns="http://www.w3.org/2000/svg" width="144" height="144" viewBox="0 0 144 144">
			<rect x="2" y="2" width="140" height="140" rx="12" fill="#07111D" stroke="${mqttColor}" stroke-width="3"/>
			<text x="72" y="62" text-anchor="middle" font-family="Arial, sans-serif" font-size="21" font-weight="bold" fill="${mqttColor}"><tspan data-part="title">MQTT: </tspan><tspan data-part="value">${!state.enabled ? "OFF" : state.connected ? "OK" : "--"}</tspan></text>
			<text x="72" y="98" text-anchor="middle" font-family="Arial, sans-serif" font-size="21" font-weight="bold" fill="${packetColor}"><tspan data-part="title">PKT: </tspan><tspan data-part="value">${state.receivedPacket ? "OK" : "--"}</tspan></text>
		</svg>`;
		return `data:image/svg+xml;charset=utf8,${encodeURIComponent(svg)}`;
	}
}
