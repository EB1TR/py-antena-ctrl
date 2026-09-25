import { action } from "@elgato/streamdeck";

import { BandAction } from "./band-action";

@action({ UUID: "com.eb1tr.tukudeck.band60" })
export class Band60 extends BandAction {
	constructor() {
		super(60, "60m");
	}
}
