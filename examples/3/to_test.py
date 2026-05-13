# This function decides the maintenance priority for a machine.
# It first validates that the numeric inputs are non-negative.
# Then it counts usage cycles through a loop, one cycle for each completed
# block of 1000 operating hours.
# After validation and cycle analysis, it classifies the maintenance need:
# - machines with no errors are normal;
# - machines with errors require inspection;
# - old machines or machines with a critical sensor require priority handling;
# - machines with many cycles receive a scheduled prefix.

def decide_maintenance(machine_age: int, operating_hours: int, error_count: int, critical_sensor: bool) -> str:
    """
    Returns a simple maintenance status for a machine.

    Rules:
    - machine_age must be >= 0
    - operating_hours must be >= 0
    - error_count must be >= 0
    - critical_sensor indicates whether a critical sensor is active
    - usage cycles are counted from operating_hours through a loop
    """

    # Validate the basic input domain.
    # This compound condition is important because each negative numeric value
    # makes the request invalid.
    if machine_age < 0 or operating_hours < 0 or error_count < 0:
        raise ValueError("Parametrii numerici nu pot fi negativi.")

    # Count completed usage cycles manually.
    # The loop is useful for structural and mutation tests because it exercises
    # repetitive behavior derived from an input parameter.
    usage_cycles = 0
    for _ in range(operating_hours // 1000):
        usage_cycles += 1

    # Apply the default classification based on reported errors.
    # This if/else branch separates machines with no errors from machines
    # that need inspection.
    if error_count == 0:
        status = "normal"
    else:
        status = "inspect"

    # Old machines or machines with a critical sensor require priority handling.
    # This compound condition intentionally has no else branch.
    if machine_age > 10 or critical_sensor:
        status = "priority"

    # Machines with many usage cycles should be scheduled explicitly.
    # This is a simple condition without an else branch.
    if usage_cycles > 5:
        status = "scheduled_" + status

    # Return the final maintenance classification.
    return status
