import streamDeck from "@elgato/streamdeck";

import { TukuTest } from "./actions/tuku-test";

import { Antenna1 } from "./actions/antenna-1";
import { Antenna2 } from "./actions/antenna-2";
import { Antenna3 } from "./actions/antenna-3";
import { Swap } from "./actions/swap";
import { Rig } from "./actions/rig";

import { Band0 } from "./actions/band-0";
import { Band160 } from "./actions/band-160";
import { Band80 } from "./actions/band-80";
import { Band60 } from "./actions/band-60";
import { Band40 } from "./actions/band-40";
import { Band30 } from "./actions/band-30";

import { BandAuto } from "./actions/band-auto";
import { Band20 } from "./actions/band-20";
import { Band17 } from "./actions/band-17";
import { Band15 } from "./actions/band-15";
import { Band12 } from "./actions/band-12";
import { Band10 } from "./actions/band-10";

import { Tw1 } from "./actions/tw1";
import { Tw2 } from "./actions/tw2";
import { Tw3 } from "./actions/tw3";

import { Tw1Park } from "./actions/tw1-park";
import { Tw1Minus5 } from "./actions/tw1-minus5";
import { Tw1Plus5 } from "./actions/tw1-plus5";

import { Tw2Park } from "./actions/tw2-park";
import { Tw2Minus5 } from "./actions/tw2-minus5";
import { Tw2Plus5 } from "./actions/tw2-plus5";

import { Tw3Park } from "./actions/tw3-park";
import { Tw3Minus5 } from "./actions/tw3-minus5";
import { Tw3Plus5 } from "./actions/tw3-plus5";

import { RotorPreset } from "./actions/rotor-preset";

import { Connection } from "./actions/connection";

import { Telemetry } from "./actions/telemetry";

import { CurrentBand } from "./actions/current-band";

import { initializeKeyDisplay } from "./key-display";

import { initializeMqtt } from "./mqtt";

streamDeck.logger.setLevel("trace");
initializeKeyDisplay();

streamDeck.actions.registerAction(new TukuTest());

streamDeck.actions.registerAction(new Antenna1());
streamDeck.actions.registerAction(new Antenna2());
streamDeck.actions.registerAction(new Antenna3());
streamDeck.actions.registerAction(new Swap());
streamDeck.actions.registerAction(new Rig());

streamDeck.actions.registerAction(new Band0());
streamDeck.actions.registerAction(new Band160());
streamDeck.actions.registerAction(new Band80());
streamDeck.actions.registerAction(new Band60());
streamDeck.actions.registerAction(new Band40());
streamDeck.actions.registerAction(new Band30());

streamDeck.actions.registerAction(new BandAuto());
streamDeck.actions.registerAction(new Band20());
streamDeck.actions.registerAction(new Band17());
streamDeck.actions.registerAction(new Band15());
streamDeck.actions.registerAction(new Band12());
streamDeck.actions.registerAction(new Band10());

streamDeck.actions.registerAction(new Tw1());
streamDeck.actions.registerAction(new Tw2());
streamDeck.actions.registerAction(new Tw3());

streamDeck.actions.registerAction(new Tw1Park());
streamDeck.actions.registerAction(new Tw1Minus5());
streamDeck.actions.registerAction(new Tw1Plus5());

streamDeck.actions.registerAction(new Tw2Park());
streamDeck.actions.registerAction(new Tw2Minus5());
streamDeck.actions.registerAction(new Tw2Plus5());

streamDeck.actions.registerAction(new Tw3Park());
streamDeck.actions.registerAction(new Tw3Minus5());
streamDeck.actions.registerAction(new Tw3Plus5());

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
