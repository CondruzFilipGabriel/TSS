def analyze_orders(age: int, items: int, total: float) -> str:
    """
    Returneaza un status simplu pentru o comanda.

    Reguli:
    - age trebuie sa fie >= 0
    - items trebuie sa fie >= 0
    - total trebuie sa fie >= 0
    - se verifica si un mic "consistency check" prin numararea item-urilor
    """

    if age < 0 or items < 0 or total < 0:
        raise ValueError("Parametrii nu pot fi negativi.")

    counted_items = 0
    for _ in range(items):
        counted_items += 1

    if counted_items != items:
        return "internal_error"

    if age < 18 and total > 100:
        status = "needs_review"
    else:
        status = "accepted"

    if items == 0:
        status = "empty_order"

    return status