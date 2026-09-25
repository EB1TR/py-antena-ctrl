import { action } from "@elgato/streamdeck";
import { RotorMoveAction } from "./rotor-move-action";

@action({ UUID: "com.eb1tr.tukudeck.tw1minus5" })
export class Tw1Minus5 extends RotorMoveAction {

	constructor() {
		super(1, "minus5");
	}
}
