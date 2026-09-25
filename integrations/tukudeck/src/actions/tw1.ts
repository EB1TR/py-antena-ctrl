import { action } from "@elgato/streamdeck";
import { RotorAction } from "./rotor-action";

@action({ UUID: "com.eb1tr.tukudeck.tw1" })
export class Tw1 extends RotorAction {
	constructor() {
		super(1);
	}
}
