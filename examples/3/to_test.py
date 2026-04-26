# This function evaluates the daily condition of a greenhouse.
# It first validates the temperature list and handles the case where no temperature
# data is available.
# Then it validates the amount of water used and processes each recorded temperature.
# During processing, it counts heat spikes, cold spikes, and stable temperature hours,
# while also computing the total temperature for the daily average.
# Finally, it classifies the greenhouse day by applying the rules in priority order:
# quarantine risk, critical heat, critical cold, optimal conditions, unstable average
# temperature, dry conditions, or general monitoring.

def evaluate_greenhouse_day(
    temperatures: list[float],
    water_liters: float,
    ventilation_on: bool,
    pest_alert: bool,
) -> str:
    # Validate that temperatures are provided as a list.
    # This branch is an important test target because non-list inputs must fail immediately.
    if not isinstance(temperatures, list):
        raise TypeError("temperatures must be a list")

    # Handle the case where no temperature readings are available.
    # This return happens before water validation and before any temperature processing.
    if len(temperatures) == 0:
        return "no_data"

    # Validate the water amount.
    # Negative water usage is outside the accepted input domain.
    if water_liters < 0:
        raise ValueError("water_liters cannot be negative")

    # Initialize counters and accumulators used to summarize the greenhouse day.
    heat_spikes = 0
    cold_spikes = 0
    stable_hours = 0
    total_temp = 0.0

    # Process each temperature reading.
    # This loop is a major test target because it validates values, updates the average,
    # and classifies each reading as hot, cold, or stable.
    for temp in temperatures:
        # Validate each temperature value.
        # Numeric values are accepted, but booleans are rejected even though bool is a subclass of int.
        if not isinstance(temp, (int, float)) or isinstance(temp, bool):
            raise TypeError("temperature values must be numeric")

        # Accumulate temperature values for the final average calculation.
        total_temp += temp

        # Count high temperature spikes.
        # Values strictly greater than 34 are treated as heat spikes.
        if temp > 34:
            heat_spikes += 1

        # Count low temperature spikes.
        # Values strictly lower than 10 are treated as cold spikes.
        elif temp < 10:
            cold_spikes += 1

        # Count all remaining readings as stable hours.
        # This includes boundary values 10 and 34.
        else:
            stable_hours += 1

    # Compute the average temperature after all readings have been validated and processed.
    average_temp = total_temp / len(temperatures)

    # Quarantine has the highest priority when pests are present and the average temperature is high.
    if pest_alert and average_temp > 28:
        return "quarantine"

    # Critical heat is reported when there are at least three heat spikes and ventilation is off.
    if heat_spikes >= 3 and not ventilation_on:
        return "critical_heat"

    # Critical cold is reported when there are at least two cold spikes and water usage is very low.
    if cold_spikes >= 2 and water_liters < 5:
        return "critical_cold"

    # Optimal conditions require all readings to be stable and water usage to be within the target range.
    if stable_hours == len(temperatures) and 8 <= water_liters <= 15:
        return "optimal"

    # An extreme average temperature marks the day as unstable.
    # This check happens after the more specific critical and optimal classifications.
    if average_temp > 30 or average_temp < 12:
        return "unstable"

    # A valid day with zero water usage is classified as dry.
    if water_liters == 0:
        return "dry"

    # If no specific rule matches, the greenhouse should continue to be monitored.
    return "monitor"