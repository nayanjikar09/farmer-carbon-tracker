# Core business calculations (kept simple + documented)

def estimate_collection_cost(total_tonnes: float) -> float:
    """₹500 base per trip + ₹300 per tonne."""
    return round(500 + 300 * total_tonnes, 2)


def biochar_from_biomass(biomass: float) -> float:
    """Typical pyrolysis yield ≈ 30%."""
    return round(biomass * 0.30, 3)


def carbon_stored(biochar: float) -> float:
    """Conservative 70% carbon content in biochar."""
    return round(biochar * 0.70, 3)


def farmer_payment(tonnes: float) -> float:
    """₹800 per tonne of waste supplied."""
    return round(tonnes * 800, 2)