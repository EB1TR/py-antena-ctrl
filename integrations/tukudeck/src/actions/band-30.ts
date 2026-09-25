import { action } from "@elgato/streamdeck";

import { BandAction } from "./band-action";

@action({ UUID: "com.eb1tr.tukudeck.band30" })
export class Band30 extends BandAction {
	constructor() {
		super(30, "30m");
	}
}
