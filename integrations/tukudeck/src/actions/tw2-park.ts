import { action } from "@elgato/streamdeck";
import { RotorMoveAction } from "./rotor-move-action";

@action({ UUID: "com.eb1tr.tukudeck.tw2park" })
export class Tw2Park extends RotorMoveAction {
	constructor() {
		super(2, "park");
	}
}
