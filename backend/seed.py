"""
Seed synthetic demo data into backend/data/app.db.

Usage:
    python backend/seed.py                       # only seeds if DB is empty
    python backend/seed.py --force               # wipe then reseed
    python backend/seed.py --force --farmers 500 # seed N farmers
"""
import argparse
import random
import sqlite3
import os
from datetime import date, timedelta

DB_PATH = os.path.join(os.path.dirname(__file__), "data", "app.db")

VILLAGES = [
    "Wardha", "Hinganghat", "Samudrapur", "Arvi", "Deoli",
    "Seloo", "Karanja", "Ashti", "Talegaon", "Pulgaon",
]

GPS_BASE = {
    "Wardha":     (20.7453, 78.6022),
    "Hinganghat": (20.5585, 78.8395),
    "Samudrapur": (20.6530, 78.9295),
    "Arvi":       (20.9890, 78.2290),
    "Deoli":      (20.6500, 78.4800),
    "Seloo":      (20.8490, 78.7190),
    "Karanja":    (20.4830, 78.2000),
    "Ashti":      (20.8830, 78.3500),
    "Talegaon":   (20.7200, 78.7000),
    "Pulgaon":    (20.7200, 78.3200),
}

FIRST_NAMES = [
    "Nayan", "Ramesh", "Suresh", "Ganesh", "Prakash", "Vijay",
    "Anil", "Sunil", "Rahul", "Amit", "Ravi", "Kiran",
    "Sachin", "Pravin", "Nitin", "Dinesh", "Manoj", "Sanjay",
]
LAST_NAMES = ["Patil", "Deshmukh", "Wankhede", "Ingle",
              "Khobragade", "Gaidhane", "Bhende"]


def random_gps(village: str):
    lat, lng = GPS_BASE[village]
    return (round(lat + random.uniform(-0.02, 0.02), 6),
            round(lng + random.uniform(-0.02, 0.02), 6))


def unique_name(village: str, used: set) -> str:
    """Generate a name that is unique within the given village."""
    while True:
        name = f"{random.choice(FIRST_NAMES)} {random.choice(LAST_NAMES)}"
        key = (name, village)
        if key not in used:
            used.add(key)
            return name


def table_counts(conn):
    f = conn.execute("SELECT COUNT(*) FROM farmers").fetchone()[0]
    c = conn.execute("SELECT COUNT(*) FROM collections").fetchone()[0]
    p = conn.execute("SELECT COUNT(*) FROM production_batches").fetchone()[0]
    return f, c, p


def wipe(conn):
    conn.executescript("""
        DELETE FROM production_batches;
        DELETE FROM collections;
        DELETE FROM farmers;
        DELETE FROM sqlite_sequence
            WHERE name IN ('farmers','collections','production_batches');
    """)
    conn.commit()


def seed(n_farmers: int = 100, force: bool = False):
    os.makedirs(os.path.dirname(DB_PATH), exist_ok=True)

    # ensure schema exists
    from database import init_db
    init_db()

    conn = sqlite3.connect(DB_PATH)
    cur = conn.cursor()

    # -------- SAFETY GATE --------
    f_existing, c_existing, p_existing = table_counts(conn)
    already_has_data = (f_existing + c_existing + p_existing) > 0

    if already_has_data and not force:
        print("⚠️  Database already has data — refusing to overwrite.")
        print(f"   farmers: {f_existing}, collections: {c_existing}, batches: {p_existing}")
        print("   Use --force to wipe and reseed.")
        conn.close()
        return

    if already_has_data and force:
        print("⚠️  --force given: wiping existing data...")
        wipe(conn)

    # -------- FARMERS (unique name per village) --------
    used_names = set()          # (name, village) pairs already inserted
    inserted = 0
    attempts = 0
    max_attempts = n_farmers * 50   # safety guard

    while inserted < n_farmers and attempts < max_attempts:
        attempts += 1
        village = random.choice(VILLAGES)
        name = unique_name(village, used_names)
        lat, lng = random_gps(village)
        try:
            cur.execute(
                """INSERT INTO farmers
                   (name, village, acres, crop, gps_lat, gps_lng)
                   VALUES (?, ?, ?, 'Cotton', ?, ?)""",
                (name, village, round(random.uniform(1.5, 15.0), 1), lat, lng),
            )
            inserted += 1
        except sqlite3.IntegrityError:
            # collision — remove from used set so next loop can retry
            used_names.discard((name, village))
    conn.commit()

    farmer_ids = [r[0] for r in cur.execute("SELECT id FROM farmers").fetchall()]

    # -------- COLLECTIONS --------
    today = date.today()
    for fid in farmer_ids:
        for _ in range(random.randint(1, 2)):
            qty = round(random.uniform(0.5, 5.0), 2)
            coll_date = (today - timedelta(days=random.randint(0, 90))).isoformat()
            status = random.choices(["Received", "Pending"], weights=[0.7, 0.3])[0]
            actual = qty if status == "Received" else None
            payment = round(actual * 800, 2) if actual else None
            est_cost = round(500 + 300 * qty, 2)

            cur.execute(
                """INSERT INTO collections
                   (farmer_id, waste_quantity_tonnes, collection_date,
                    actual_weight_tonnes, payment_inr, estimated_cost_inr, status)
                   VALUES (?, ?, ?, ?, ?, ?, ?)""",
                (fid, qty, coll_date, actual, payment, est_cost, status),
            )
    conn.commit()

    # -------- PRODUCTION BATCHES --------
    rows = cur.execute(
        "SELECT id, actual_weight_tonnes FROM collections WHERE status='Received'"
    ).fetchall()
    for cid, actual in rows:
        if random.random() > 0.7:
            continue
        biochar = round(actual * 0.30, 3)
        carbon = round(biochar * 0.70, 3)
        batch_date = (today - timedelta(days=random.randint(0, 30))).isoformat()
        cur.execute(
            """INSERT INTO production_batches
               (collection_id, biomass_input_tonnes, biochar_output_tonnes,
                carbon_stored_tonnes, batch_date)
               VALUES (?, ?, ?, ?, ?)""",
            (cid, actual, biochar, carbon, batch_date),
        )
    conn.commit()

    f, c, p = table_counts(conn)
    conn.close()

    print(f"\n✅ Seeded {DB_PATH}")
    print(f"   farmers:             {f}")
    print(f"   collections:         {c}")
    print(f"   production_batches:  {p}")
    print("\n   Data is now permanent in app.db.")
    print("   Start server:  python run.py")


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--farmers", type=int, default=100,
                        help="Number of farmers to generate (default 100)")
    parser.add_argument("--force", action="store_true",
                        help="Wipe existing data and reseed")
    args = parser.parse_args()

    seed(n_farmers=args.farmers, force=args.force)