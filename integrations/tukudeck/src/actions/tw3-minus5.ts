import { action } from "@elgato/streamdeck";
import { RotorMoveAction } from "./rotor-move-action";

@action({ UUID: "com.eb1tr.tukudeck.tw3minus5" })
export class Tw3Minus5 extends RotorMoveAction {
	constructor() {
		super(3, "minus5");
	}
}
