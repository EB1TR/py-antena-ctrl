import {
	action
} from "@elgato/streamdeck";

import { AntennaAction } from "./antenna-action";

@action({ UUID: "com.eb1tr.tukudeck.antenna1" })
export class Antenna1 extends AntennaAction {
	constructor() {
		super(1);
	}
}