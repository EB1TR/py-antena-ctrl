import { action } from "@elgato/streamdeck";

import { BandAction } from "./band-action";

@action({ UUID: "com.eb1tr.tukudeck.band15" })
export class Band15 extends BandAction {
	constructor() {
		super(15, "15m");
	}
}
