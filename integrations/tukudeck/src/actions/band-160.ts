import { action } from "@elgato/streamdeck";

import { BandAction } from "./band-action";

@action({ UUID: "com.eb1tr.tukudeck.band160" })
export class Band160 extends BandAction {
	constructor() {
		super(160, "160m");
	}
}
