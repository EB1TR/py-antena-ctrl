import { action } from "@elgato/streamdeck";

import { BandAction } from "./band-action";

@action({ UUID: "com.eb1tr.tukudeck.band0" })
export class Band0 extends BandAction {
	constructor() {
		super(0, "N/A");
	}
}
