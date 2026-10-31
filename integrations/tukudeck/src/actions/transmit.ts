import { action, SingletonAction, type WillAppearEvent, type WillDisappearEvent, type DidReceiveSettingsEvent, type KeyDownEvent } from "@elgato/streamdeck";
import { setKeyImage } from "../key-display";
import { sendCommand } from "../mqtt";
import { getStation, type StationSettings } from "../station";
import { beginControl, getControlState, onControlState, type TransmitControl } from "../transmit-control";

type ControlSettings = StationSettings & { offsetKhz?: string | number };

class TransmitAction extends SingletonAction<ControlSettings> {
    private readonly cleanups = new Map<string, () => void>();
    constructor(private readonly control: TransmitControl) { super(); }
    override async onWillAppear(ev: WillAppearEvent<ControlSettings>): Promise<void> { this.subscribe(ev); }
    override async onDidReceiveSettings(ev: DidReceiveSettingsEvent<ControlSettings>): Promise<void> { this.subscribe(ev); }
    private subscribe(ev: WillAppearEvent<ControlSettings> | DidReceiveSettingsEvent<ControlSettings>): void {
        this.cleanups.get(ev.action.id)?.();
        const station = getStation(ev.payload.settings);
        const render = () => {
            const state = getControlState(station, this.control);
            const color = state.error ? "#FF9F43" : state.active ? "#FF3B3B" : "#31AA31";
            const label = state.pending ? "ESPERANDO" : state.error ? "ERROR" : state.active === null ? "SIN DATOS" : state.active ? "ON" : this.control === "atu" ? "BYPASS" : "OFF";
            const svg = `<svg xmlns="http://www.w3.org/2000/svg" width="144" height="144"><rect x="2" y="2" width="140" height="140" rx="12" fill="#07111D" stroke="${color}" stroke-width="3"/><text data-part="title" x="72" y="58" text-anchor="middle" font-family="Arial" font-size="32" font-weight="bold" fill="${color}">${this.control.toUpperCase()}</text><text data-part="value" x="72" y="94" text-anchor="middle" font-family="Arial" font-size="18" fill="${color}">${label}</text><text data-part="station" x="72" y="125" text-anchor="middle" font-family="Arial" font-size="15" fill="#A0A0A0">${station.toUpperCase()}</text></svg>`;
            void setKeyImage(ev.action, `data:image/svg+xml;charset=utf8,${encodeURIComponent(svg)}`, state.active === null);
        };
        this.cleanups.set(ev.action.id, onControlState(render));
        render();
    }
    override onWillDisappear(ev: WillDisappearEvent<ControlSettings>): void {
        this.cleanups.get(ev.action.id)?.(); this.cleanups.delete(ev.action.id);
    }
    override async onKeyDown(ev: KeyDownEvent<ControlSettings>): Promise<void> {
        const station = getStation(ev.payload.settings), state = getControlState(station, this.control);
        const offsetHz = Math.round(Number(ev.payload.settings.offsetKhz ?? 1) * 1000);
        if (this.control === "split" && (!Number.isFinite(offsetHz) || Math.abs(offsetHz) < 1 || Math.abs(offsetHz) > 100000)) { await ev.action.showAlert(); return; }
        if (!beginControl(station, this.control)) { if (!state.pending) await ev.action.showAlert(); return; }
        sendCommand(`set/${station}/${this.control}`, this.control === "split" ? JSON.stringify({ enabled: state.active ? 0 : 1, offset_hz: offsetHz }) : this.control === "atu" ? (state.active ? "bypass" : "start") : (state.active ? 0 : 1));
    }
}
@action({ UUID: "com.eb1tr.tukudeck.mox" })
export class Mox extends TransmitAction { constructor() { super("mox"); } }
@action({ UUID: "com.eb1tr.tukudeck.tune" })
export class Tune extends TransmitAction { constructor() { super("tune"); } }

@action({ UUID: "com.eb1tr.tukudeck.atu" })
export class Atu extends TransmitAction { constructor() { super("atu"); } }

@action({ UUID: "com.eb1tr.tukudeck.split" })
export class Split extends TransmitAction { constructor() { super("split"); } }
