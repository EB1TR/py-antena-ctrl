import { action } from "@elgato/streamdeck";
import { RotorAction } from "./rotor-action";

@action({ UUID: "com.eb1tr.tukudeck.tw3" })
export class Tw3 extends RotorAction {
	constructor() {
		super(3);
	}
}
