import { action } from "@elgato/streamdeck";
import { RotorMoveAction } from "./rotor-move-action";

@action({ UUID: "com.eb1tr.tukudeck.tw2minus5" })
export class Tw2Minus5 extends RotorMoveAction {
	constructor() {
		super(2, "minus5");
	}
}
