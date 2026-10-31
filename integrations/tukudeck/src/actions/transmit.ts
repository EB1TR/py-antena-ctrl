import { action, SingletonAction, type WillAppearEvent, type WillDisappearEvent, type DidReceiveSettingsEvent, type KeyDownEvent, type KeyUpEvent } from "@elgato/streamdeck";
import { setKeyImage } from "../key-display";
import { sendCommand } from "../mqtt";
import { getStation, type StationSettings } from "../station";
import { beginControl, getControlState, onControlState, type TransmitControl } from "../transmit-control";

type ControlSettings = StationSettings & { offsetKhz?: string | number; muteB?: "yes" | "no" | boolean; volumeA?: string | number; volumeB?: string | number; balanceA?: string | number; balanceB?: string | number };

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
            const sliceButton = /^(mute|rx|tx)[ab]$/.test(this.control);
            const missing = sliceButton && state.exists === false;
            let color: string;
            if (state.error) color = "#FF9F43";
            else if (missing || state.active === null) color = "#FFFFFF";
            else if (this.control.startsWith("mute")) color = state.active ? "#FF3B3B" : "#31AA31";
            else if (this.control === "rxa" || this.control === "rxb") color = state.active ? "#31AA31" : "#808080";
            else if (this.control === "txa" || this.control === "txb") color = state.active ? "#FF3B3B" : "#808080";
            else if (this.control === "atu") color = state.tuning ? "#FF3B3B" : state.active ? "#31AA31" : "#FFFFFF";
            else if (this.control === "a_eq_b") color = state.active ? "#31AA31" : "#FFFFFF";
            else color = state.active ? "#FF3B3B" : "#31AA31";
            const label = state.pending ? "ESPERANDO" : state.error ? "ERROR" : missing ? "NO EXISTE" : state.active === null ? "SIN DATOS" : state.tuning && this.control === "atu" ? "SINTONIZANDO" : state.active ? "ON" : this.control === "atu" ? "BYPASS" : "OFF";
            const svg = `<svg xmlns="http://www.w3.org/2000/svg" width="144" height="144"><rect x="2" y="2" width="140" height="140" rx="12" fill="#07111D" stroke="${color}" stroke-width="3"/><text data-part="title" x="72" y="58" text-anchor="middle" font-family="Arial" font-size="32" font-weight="bold" fill="${color}">${({mutea:"MUTE A",muteb:"MUTE B",rxa:"RX A",rxb:"RX B",txa:"TX A",txb:"TX B",a_eq_b:"A=B"} as Record<string,string>)[this.control] ?? this.control.toUpperCase()}</text><text data-part="value" x="72" y="94" text-anchor="middle" font-family="Arial" font-size="18" fill="${color}">${label}</text><text data-part="station" x="72" y="125" text-anchor="middle" font-family="Arial" font-size="15" fill="#A0A0A0">${station.toUpperCase()}</text></svg>`;
            void setKeyImage(ev.action, `data:image/svg+xml;charset=utf8,${encodeURIComponent(svg)}`, state.active === null && !missing);
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
        const audio: Record<string, number> = {};
        if (this.control === "split" && !state.active) {
            for (const [setting, field] of [["volumeA", "volume_a"], ["volumeB", "volume_b"], ["balanceA", "balance_a"], ["balanceB", "balance_b"]] as const) {
                const raw = ev.payload.settings[setting];
                if (raw === undefined || String(raw).trim() === "") continue;
                const value = Number(raw);
                if (!Number.isInteger(value) || value < 0 || value > 100) { await ev.action.showAlert(); return; }
                audio[field] = value;
            }
        }
        if (!beginControl(station, this.control)) { if (!state.pending) await ev.action.showAlert(); return; }
        sendCommand(`set/${station}/${this.control}`, this.control === "split" ? JSON.stringify({ enabled: state.active ? 0 : 1, offset_hz: offsetHz, mute_b: ev.payload.settings.muteB === "yes" || ev.payload.settings.muteB === true, ...audio }) : this.control === "atu" ? (state.active ? "bypass" : "start") : (["rxa", "rxb", "txa", "txb", "a_eq_b"].includes(this.control) ? 1 : state.active ? 0 : 1));
    }
}
@action({ UUID: "com.eb1tr.tukudeck.mox" })
export class Mox extends TransmitAction { constructor() { super("mox"); } }
@action({ UUID: "com.eb1tr.tukudeck.tune" })
export class Tune extends TransmitAction { constructor() { super("tune"); } }

@action({ UUID: "com.eb1tr.tukudeck.atu" })
export class Atu extends TransmitAction {
    private readonly presses = new Map<string, { started: number; station: ReturnType<typeof getStation>; wasOn: boolean }>();
    constructor() { super("atu"); }
    override async onKeyDown(ev: KeyDownEvent<ControlSettings>): Promise<void> {
        if (this.presses.has(ev.action.id)) return;
        const station = getStation(ev.payload.settings), state = getControlState(station, "atu");
        if (state.pending) return;
        this.presses.set(ev.action.id, { started: Date.now(), station, wasOn: state.active === true });
    }
    override async onKeyUp(ev: KeyUpEvent<ControlSettings>): Promise<void> {
        const press = this.presses.get(ev.action.id);
        this.presses.delete(ev.action.id);
        if (!press || press.station !== getStation(ev.payload.settings)) return;
        const long = Date.now() - press.started >= 700;
        const state = getControlState(press.station, "atu");
        if (long && (!press.wasOn || state.active !== true)) return;
        if (!beginControl(press.station, "atu")) { if (!state.pending) await ev.action.showAlert(); return; }
        sendCommand(`set/${press.station}/atu`, long ? "bypass" : "start");
    }
    override async onDidReceiveSettings(ev: DidReceiveSettingsEvent<ControlSettings>): Promise<void> {
        this.presses.delete(ev.action.id); await super.onDidReceiveSettings(ev);
    }
    override onWillDisappear(ev: WillDisappearEvent<ControlSettings>): void {
        this.presses.delete(ev.action.id); super.onWillDisappear(ev);
    }
}

@action({ UUID: "com.eb1tr.tukudeck.split" })
export class Split extends TransmitAction { constructor() { super("split"); } }

@action({ UUID: "com.eb1tr.tukudeck.mutea" })
export class Mutea extends TransmitAction { constructor() { super("mutea"); } }

@action({ UUID: "com.eb1tr.tukudeck.muteb" })
export class Muteb extends TransmitAction { constructor() { super("muteb"); } }

@action({ UUID: "com.eb1tr.tukudeck.rxa" })
export class Rxa extends TransmitAction { constructor() { super("rxa"); } }

@action({ UUID: "com.eb1tr.tukudeck.rxb" })
export class Rxb extends TransmitAction { constructor() { super("rxb"); } }

@action({ UUID: "com.eb1tr.tukudeck.txa" })
export class Txa extends TransmitAction { constructor() { super("txa"); } }

@action({ UUID: "com.eb1tr.tukudeck.txb" })
export class Txb extends TransmitAction { constructor() { super("txb"); } }

@action({ UUID: "com.eb1tr.tukudeck.a-eq-b" })
export class AEqB extends TransmitAction { constructor() { super("a_eq_b"); } }
