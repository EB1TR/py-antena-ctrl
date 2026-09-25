import { action } from "@elgato/streamdeck";

import { BandAction } from "./band-action";

@action({ UUID: "com.eb1tr.tukudeck.band20" })
export class Band20 extends BandAction {
	constructor() {
		super(20, "20m");
	}
}
