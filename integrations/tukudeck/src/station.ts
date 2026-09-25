export type Station = "stn1" | "stn2";

export type StationSettings = {
	station?: Station;
};

export function getStation(settings: StationSettings): Station {
	return settings.station === "stn1" ? "stn1" : "stn2";
}
