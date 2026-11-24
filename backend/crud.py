from database import get_conn
from carbon import (
    estimate_collection_cost, farmer_payment,
    biochar_from_biomass, carbon_stored,
)


# ---------- FARMERS ----------
def create_farmer(data):
    conn = get_conn()
    cur = conn.execute(
        """INSERT INTO farmers (name, village, acres, crop, gps_lat, gps_lng)
           VALUES (?, ?, ?, ?, ?, ?)""",
        (data.name, data.village, data.acres, data.crop, data.gps_lat, data.gps_lng),
    )
    conn.commit()
    fid = cur.lastrowid
    conn.close()
    return {"id": fid, **data.model_dump()}


def list_farmers():
    conn = get_conn()
    rows = conn.execute("SELECT * FROM farmers ORDER BY id DESC").fetchall()
    conn.close()
    return [dict(r) for r in rows]


def farmer_payment_report():
    """Payment summary per farmer (Question #7)."""
    conn = get_conn()
    rows = conn.execute("""
        SELECT f.id, f.name, f.village, f.acres,
               COUNT(c.id)                                        AS collections_count,
               ROUND(SUM(COALESCE(c.actual_weight_tonnes, 0)),2)  AS delivered_tonnes,
               ROUND(SUM(COALESCE(c.payment_inr, 0)),2)           AS total_payment_inr
        FROM farmers f
        LEFT JOIN collections c ON c.farmer_id = f.id
        GROUP BY f.id
        ORDER BY total_payment_inr DESC
    """).fetchall()
    conn.close()
    return [dict(r) for r in rows]


# ---------- COLLECTIONS ----------
def create_collection(data):
    cost = estimate_collection_cost(data.waste_quantity_tonnes)
    pay = farmer_payment(data.waste_quantity_tonnes)
    conn = get_conn()
    cur = conn.execute(
        """INSERT INTO collections
           (farmer_id, waste_quantity_tonnes, collection_date,
            estimated_cost_inr, payment_inr, status)
           VALUES (?, ?, ?, ?, ?, 'Pending')""",
        (data.farmer_id, data.waste_quantity_tonnes, data.collection_date, cost, pay),
    )
    conn.commit()
    cid = cur.lastrowid
    conn.close()
    return {"id": cid, "estimated_cost_inr": cost, "payment_inr": pay, **data.model_dump()}


def list_collections():
    conn = get_conn()
    rows = conn.execute("""
        SELECT c.*, f.name AS farmer_name, f.village
        FROM collections c
        JOIN farmers f ON f.id = c.farmer_id
        ORDER BY f.village, c.id DESC
    """).fetchall()
    conn.close()
    return [dict(r) for r in rows]


def mark_received(collection_id: int, actual_weight: float):
    pay = farmer_payment(actual_weight)
    conn = get_conn()
    conn.execute(
        """UPDATE collections
           SET actual_weight_tonnes=?, payment_inr=?, status='Received'
           WHERE id=?""",
        (actual_weight, pay, collection_id),
    )
    conn.commit()
    conn.close()
    return {"id": collection_id, "status": "Received",
            "actual_weight_tonnes": actual_weight, "payment_inr": pay}


def recommend_route():
    """Villages ordered by priority for collection (Question #3)."""
    conn = get_conn()
    rows = conn.execute("""
        SELECT f.village,
               COUNT(c.id)                            AS pending_count,
               ROUND(SUM(c.waste_quantity_tonnes), 2) AS total_tonnes,
               ROUND(SUM(c.estimated_cost_inr), 2)    AS total_cost,
               ROUND(AVG(f.gps_lat), 6)               AS avg_lat,
               ROUND(AVG(f.gps_lng), 6)               AS avg_lng
        FROM collections c
        JOIN farmers f ON f.id = c.farmer_id
        WHERE c.status = 'Pending'
        GROUP BY f.village
    """).fetchall()
    conn.close()

    villages = []
    for r in rows:
        score = round(r["total_tonnes"] * 10 - r["total_cost"], 2)
        villages.append({
            "village":        r["village"],
            "pending_count":  r["pending_count"],
            "total_tonnes":   r["total_tonnes"],
            "total_cost":     r["total_cost"],
            "avg_lat":        r["avg_lat"],
            "avg_lng":        r["avg_lng"],
            "priority_score": score,
        })

    villages.sort(key=lambda v: v["priority_score"], reverse=True)
    for i, v in enumerate(villages, start=1):
        v["visit_order"] = i

    return {"route": villages, "total_villages": len(villages)}


# ---------- PRODUCTION ----------
def create_batch(data):
    biochar = biochar_from_biomass(data.biomass_input_tonnes)
    carbon = carbon_stored(biochar)
    conn = get_conn()
    cur = conn.execute(
        """INSERT INTO production_batches
           (collection_id, biomass_input_tonnes, biochar_output_tonnes,
            carbon_stored_tonnes, batch_date)
           VALUES (?, ?, ?, ?, ?)""",
        (data.collection_id, data.biomass_input_tonnes,
         biochar, carbon, data.batch_date),
    )
    conn.commit()
    bid = cur.lastrowid
    conn.close()
    return {"id": bid, "biochar_output_tonnes": biochar,
            "carbon_stored_tonnes": carbon, **data.model_dump()}


def list_batches():
    conn = get_conn()
    rows = conn.execute(
        "SELECT * FROM production_batches ORDER BY id DESC"
    ).fetchall()
    conn.close()
    return [dict(r) for r in rows]


def production_report():
    """Batch-by-batch production + grand totals (Question #13)."""
    conn = get_conn()
    batches = conn.execute("""
        SELECT b.id, b.batch_date,
               b.biomass_input_tonnes, b.biochar_output_tonnes,
               b.carbon_stored_tonnes,
               f.village, f.name AS farmer_name
        FROM production_batches b
        LEFT JOIN collections c ON c.id = b.collection_id
        LEFT JOIN farmers f     ON f.id = c.farmer_id
        ORDER BY b.batch_date DESC
    """).fetchall()

    totals = conn.execute("""
        SELECT ROUND(COALESCE(SUM(biomass_input_tonnes),0),2)  AS biomass,
               ROUND(COALESCE(SUM(biochar_output_tonnes),0),2) AS biochar,
               ROUND(COALESCE(SUM(carbon_stored_tonnes),0),2)  AS carbon
        FROM production_batches
    """).fetchone()
    conn.close()

    return {
        "batches": [dict(r) for r in batches],
        "totals":  dict(totals),
    }


# ---------- DASHBOARD ----------
def dashboard_summary():
    conn = get_conn()

    farmers_count = conn.execute("SELECT COUNT(*) FROM farmers").fetchone()[0]

    biomass_received = conn.execute(
        "SELECT COALESCE(SUM(actual_weight_tonnes),0) FROM collections WHERE status='Received'"
    ).fetchone()[0]

    biochar_total = conn.execute(
        "SELECT COALESCE(SUM(biochar_output_tonnes),0) FROM production_batches"
    ).fetchone()[0]

    carbon_total = conn.execute(
        "SELECT COALESCE(SUM(carbon_stored_tonnes),0) FROM production_batches"
    ).fetchone()[0]

    collection_records = conn.execute("""
        SELECT f.village,
               ROUND(SUM(COALESCE(c.actual_weight_tonnes, c.waste_quantity_tonnes)),2) AS biomass_t,
               CASE
                 WHEN SUM(CASE WHEN c.status='Pending' THEN 1 ELSE 0 END) > 0 THEN 'Pending'
                 ELSE 'Received'
               END AS status
        FROM collections c
        JOIN farmers f ON f.id = c.farmer_id
        GROUP BY f.village
        ORDER BY f.village
    """).fetchall()

    biomass_processed = conn.execute(
        "SELECT COALESCE(SUM(biomass_input_tonnes),0) FROM production_batches"
    ).fetchone()[0]

    # ---- Next pickup village - uses SAME priority score as /route ----
    # score = (total_tonnes × 10) − total_cost  (higher = visit first)
    next_rows = conn.execute("""
        SELECT f.village,
               ROUND(SUM(c.waste_quantity_tonnes),2) AS tonnes,
               ROUND(SUM(c.estimated_cost_inr),2)    AS cost
        FROM collections c
        JOIN farmers f ON f.id = c.farmer_id
        WHERE c.status = 'Pending'
        GROUP BY f.village
    """).fetchall()

    next_village = None
    if next_rows:
        scored = [
            {
                "village": r["village"],
                "tonnes":  r["tonnes"],
                "priority_score": round(r["tonnes"] * 10 - r["cost"], 2),
            }
            for r in next_rows
        ]
        scored.sort(key=lambda x: x["priority_score"], reverse=True)
        top = scored[0]
        next_village = {"village": top["village"], "tonnes": top["tonnes"]}

    conn.close()

    return {
        "farmers_registered":       farmers_count,
        "biomass_collected_t":      round(biomass_received, 2),
        "biochar_produced_t":       round(biochar_total, 2),
        "estimated_gross_carbon_t": round(carbon_total, 2),
        "collection_records":       [dict(r) for r in collection_records],
        "production": {
            "biomass_processed_t": round(biomass_processed, 2),
            "biochar_produced_t":  round(biochar_total, 2),
        },
        "carbon_monitoring": "Awaiting verification",
        "next_village":      next_village,
    }