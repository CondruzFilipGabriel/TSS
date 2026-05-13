# This function classifies a delivery request and returns a status string.
# It first validates that the numeric inputs are non-negative.
# Then it counts route checkpoints through a loop, using one checkpoint for
# every started 50 km segment of the delivery route.
# After validation and route analysis, it classifies the delivery:
# - light deliveries have weight up to 5 kg;
# - heavier deliveries are classified as heavy;
# - fragile deliveries over long distances require special handling;
# - routes with many checkpoints receive a long-route suffix.

def classify_delivery(weight_kg: int, distance_km: int, fragile: bool) -> str:
    """
    Returns a simple classification for a delivery request.

    Rules:
    - weight_kg must be >= 0
    - distance_km must be >= 0
    - fragile indicates whether the package needs extra care
    - distance is analyzed through a small loop that counts 50 km checkpoints
    """

    # Validate the basic input domain.
    # This compound condition is an important test target because any negative
    # numeric parameter must stop the function immediately.
    if weight_kg < 0 or distance_km < 0:
        raise ValueError("Parametrii numerici nu pot fi negativi.")

    # Count route checkpoints manually in order to create a simple repetitive path.
    # The loop is useful for tests because mutations may change the step, the range,
    # or the final checkpoint count.
    checkpoints = 0
    for _ in range(0, distance_km, 50):
        checkpoints += 1

    # Apply the main weight classification.
    # This if/else is a key branch because it separates normal light packages
    # from heavier packages.
    if weight_kg <= 5:
        status = "light"
    else:
        status = "heavy"

    # Fragile long-distance deliveries require a special status.
    # This branch uses a compound condition and intentionally has no else block.
    if fragile and distance_km > 100:
        status = "special_handling"

    # Long routes keep the previous classification, but add extra context.
    # This is a simple condition without an else branch.
    if checkpoints > 3:
        status = status + "_long_route"

    # Return the final classification after all rule checks.
    return status
