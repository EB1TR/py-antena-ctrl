import { action } from "@elgato/streamdeck";
import { RotorMoveAction } from "./rotor-move-action";

@action({ UUID: "com.eb1tr.tukudeck.tw3plus5" })
export class Tw3Plus5 extends RotorMoveAction {
	constructor() {
		super(3, "plus5");
	}
}
