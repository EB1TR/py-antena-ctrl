import { action } from "@elgato/streamdeck";

import { BandAction } from "./band-action";

@action({ UUID: "com.eb1tr.tukudeck.band40" })
export class Band40 extends BandAction {
	constructor() {
		super(40, "40m");
	}
}
