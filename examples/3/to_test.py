def evaluate_greenhouse_day(
    temperatures: list[float],
    water_liters: float,
    ventilation_on: bool,
    pest_alert: bool,
) -> str:
    if not isinstance(temperatures, list):
        raise TypeError("temperatures must be a list")

    if len(temperatures) == 0:
        return "no_data"

    if water_liters < 0:
        raise ValueError("water_liters cannot be negative")

    heat_spikes = 0
    cold_spikes = 0
    stable_hours = 0
    total_temp = 0.0

    for temp in temperatures:
        if not isinstance(temp, (int, float)) or isinstance(temp, bool):
            raise TypeError("temperature values must be numeric")

        total_temp += temp

        if temp > 34:
            heat_spikes += 1
        elif temp < 10:
            cold_spikes += 1
        else:
            stable_hours += 1

    average_temp = total_temp / len(temperatures)

    if pest_alert and average_temp > 28:
        return "quarantine"

    if heat_spikes >= 3 and not ventilation_on:
        return "critical_heat"

    if cold_spikes >= 2 and water_liters < 5:
        return "critical_cold"

    if stable_hours == len(temperatures) and 8 <= water_liters <= 15:
        return "optimal"

    if average_temp > 30 or average_temp < 12:
        return "unstable"

    if water_liters == 0:
        return "dry"

    return "monitor"