import { action } from "@elgato/streamdeck";

import { BandAction } from "./band-action";

@action({ UUID: "com.eb1tr.tukudeck.band80" })
export class Band80 extends BandAction {
	constructor() {
		super(80, "80m");
	}
}
