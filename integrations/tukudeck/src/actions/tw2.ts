import { action } from "@elgato/streamdeck";
import { RotorAction } from "./rotor-action";

@action({ UUID: "com.eb1tr.tukudeck.tw2" })
export class Tw2 extends RotorAction {
	constructor() {
		super(2);
	}
}
