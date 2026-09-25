import { action } from "@elgato/streamdeck";
import { RotorMoveAction } from "./rotor-move-action";

@action({ UUID: "com.eb1tr.tukudeck.tw1park" })
export class Tw1Park extends RotorMoveAction {

	constructor() {
		super(1, "park");
	}
}
