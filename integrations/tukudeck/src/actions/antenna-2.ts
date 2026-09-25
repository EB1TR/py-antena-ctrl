import {
	action
} from "@elgato/streamdeck";

import { AntennaAction } from "./antenna-action";

@action({ UUID: "com.eb1tr.tukudeck.antenna2" })
export class Antenna2 extends AntennaAction {
	constructor() {
		super(2);
	}
}