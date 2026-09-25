import streamDeck from "@elgato/streamdeck";

import { AntennaAction } from "./actions/antenna-action";
import { Swap } from "./actions/swap";
import { Rig } from "./actions/rig";

import { BandAction } from "./actions/band-action";

import { BandAuto } from "./actions/band-auto";

import { RotorAction } from "./actions/rotor-action";

import { RotorMoveAction } from "./actions/rotor-move-action";

import { RotorPreset } from "./actions/rotor-preset";

import { Connection } from "./actions/connection";

import { Telemetry } from "./actions/telemetry";

import { CurrentBand } from "./actions/current-band";

import { initializeKeyDisplay } from "./key-display";

import { initializeMqtt } from "./mqtt";

streamDeck.logger.setLevel("trace");
initializeKeyDisplay();

streamDeck.actions.registerAction(new AntennaAction(1));
streamDeck.actions.registerAction(new Swap());
streamDeck.actions.registerAction(new Rig());

streamDeck.actions.registerAction(new BandAction(0, "N/A"));

streamDeck.actions.registerAction(new BandAuto());

streamDeck.actions.registerAction(new RotorAction(1));

streamDeck.actions.registerAction(new RotorMoveAction());

streamDeck.actions.registerAction(new RotorPreset());

streamDeck.actions.registerAction(new CurrentBand());
streamDeck.actions.registerAction(new Telemetry());
streamDeck.actions.registerAction(new Connection());

async function startPlugin(): Promise<void> {
	await streamDeck.connect();
	const settings = await streamDeck.settings.getGlobalSettings<{ mqttStartup?: string }>();
	initializeMqtt(settings.mqttStartup !== "disconnected");
}

void startPlugin().catch((error: unknown) => {
	streamDeck.logger.error(`Error al iniciar el plugin: ${String(error)}`);
});
