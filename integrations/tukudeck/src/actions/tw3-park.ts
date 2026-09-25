import { action } from "@elgato/streamdeck";
import { RotorMoveAction } from "./rotor-move-action";

@action({ UUID: "com.eb1tr.tukudeck.tw3park" })
export class Tw3Park extends RotorMoveAction {
	constructor() {
		super(3, "park");
	}
}
