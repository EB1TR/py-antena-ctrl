import {
	action
} from "@elgato/streamdeck";

import { AntennaAction } from "./antenna-action";

@action({ UUID: "com.eb1tr.tukudeck.antenna3" })
export class Antenna3 extends AntennaAction {
	constructor() {
		super(3);
	}
}