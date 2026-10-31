import type { Station } from "./station";

export type TransmitControl = "mox" | "tune" | "atu" | "split" | "mutea" | "muteb" | "rxa" | "rxb" | "txa" | "txb" | "a_eq_b";
export type ControlState = { active: boolean | null; pending: boolean; exists?: boolean; tuning?: boolean; error?: string };
const states = new Map<string, ControlState>();
const timers = new Map<string, ReturnType<typeof setTimeout>>();
const heartbeats = new Map<Station, ReturnType<typeof setTimeout>>();
const listeners = new Set<() => void>();
const key = (station: Station, control: TransmitControl) => `${station}/${control}`;
const notify = () => { for (const listener of listeners) listener(); };
export function getControlState(station: Station, control: TransmitControl): ControlState {
    const state = { ...(states.get(key(station, control)) ?? { active: null, pending: false }) };
    if (!heartbeats.has(station)) { state.active = null; state.exists = undefined; }
    return state;
}
export function onControlState(listener: () => void): () => void {
    listeners.add(listener);
    return () => { listeners.delete(listener); };
}
function clearPending(id: string): void {
    const timer = timers.get(id);
    if (timer !== undefined) clearTimeout(timer);
    timers.delete(id);
}
export function resetTransmitControls(): void {
    for (const timer of timers.values()) clearTimeout(timer);
    for (const timer of heartbeats.values()) clearTimeout(timer);
    timers.clear(); heartbeats.clear(); states.clear(); notify();
}
export function beginControl(station: Station, control: TransmitControl): boolean {
    const id = key(station, control), state = getControlState(station, control);
    const canCreate = state.exists === false && ["rxa", "rxb", "txb"].includes(control) && getControlState(station, "mox").active === false;
    if (state.pending || (!canCreate && state.active === null && (control !== "atu" || getControlState(station, "mox").active !== false))) return false;
    states.set(id, { ...state, pending: true, error: undefined });
    timers.set(id, setTimeout(() => {
        states.set(id, { ...getControlState(station, control), pending: false, error: "Sin respuesta" });
        timers.delete(id); notify();
    }, control === "split" ? 20000 : 7000));
    notify(); return true;
}
export function processTransmitControl(topic: string, payload: string): void {
    const atu = /^(stn[12])\/atu\/state$/.exec(topic);
    if (atu) {
        try {
            const data = JSON.parse(payload) as { enabled?: string; atu_enabled?: string; status?: string };
            const status = (data.status ?? "").toUpperCase();
            const enabled = data.atu_enabled ?? data.enabled;
            const active = status.includes("BYPASS") ? false : status === "TUNE_IN_PROGRESS" ? true : enabled === "1" ? true : enabled === "0" ? false : null;
            if (active !== null) {
                const station = atu[1] as Station;
                states.set(key(station, "atu"), { ...getControlState(station, "atu"), active, tuning: status === "TUNE_IN_PROGRESS" }); notify();
            }
        } catch { /* Ignore malformed ATU telemetry. */ }
        return;
    }
    const match = /^(stn[12])\/(tx|tune|mox|atu|split|mutea|muteb|rxa|rxb|txa|txb|a_eq_b)(\/result)?$/.exec(topic);
    if (!match) return;
    const station = match[1] as Station;
    const control = match[2] === "tx" ? "mox" : match[2] as TransmitControl;
    const id = key(station, control);
    if (match[3]) {
        if (match[2] === "tx") return;
        try {
            const result = JSON.parse(payload) as { status: string; value: string };
            if (!getControlState(station, control).pending) return;
            clearPending(id);
            const old = getControlState(station, control);
            const accepted = result.status === "accepted" && (control === "atu" ? ["start", "bypass"].includes(result.value) : ["0", "1"].includes(result.value));
            // MOX is displayed from actual interlock TX, never from an acknowledgment.
            states.set(id, { ...old, active: accepted && (control === "atu" || control === "tune") ? (control === "atu" ? result.value === "start" : result.value === "1") : old.active,
                tuning: control === "atu" && accepted && result.value === "bypass" ? false : old.tuning, pending: false, error: accepted ? undefined : result.status });
            notify();
        } catch { /* Ignore malformed replies. */ }
        return;
    }
    if (payload === "absent" && /^(mute|rx|tx)[ab]$/.test(control)) {
        clearPending(id);
        states.set(id, { active: null, exists: false, pending: false }); notify(); return;
    }
    if (payload === "unknown") {
        states.set(id, { ...getControlState(station, control), active: null, exists: undefined }); notify(); return;
    }
    if (payload !== "0" && payload !== "1") return;
    if (match[2] === "tx") {
        const previous = heartbeats.get(station);
        if (previous !== undefined) clearTimeout(previous);
        heartbeats.set(station, setTimeout(() => {
            for (const action of ["mox", "tune", "atu", "split", "mutea", "muteb", "rxa", "rxb", "txa", "txb", "a_eq_b"] as const) {
                const target = key(station, action); clearPending(target);
                states.set(target, { active: null, pending: false });
            }
            heartbeats.delete(station); notify();
        }, 5000));
        if (payload === "0") states.set(key(station, "tune"), { ...getControlState(station, "tune"), active: false });
    }
    states.set(id, { ...getControlState(station, control), active: payload === "1", exists: true });
    notify();
}
