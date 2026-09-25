import { action } from "@elgato/streamdeck";

import { BandAction } from "./band-action";

@action({ UUID: "com.eb1tr.tukudeck.band10" })
export class Band10 extends BandAction {
	constructor() {
		super(10, "10m");
	}
}
