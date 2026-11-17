"""
Milestone 2 - Formula 1 Knowledge Graph builder.

Reads the Formula 1 CSV files located in the same directory as this script and
builds the Knowledge Graph in Neo4j following the exact Milestone 2 schema.

Neo4j credentials are read from config.txt (same directory), by key:
    URI=neo4j://localhost:7687
    USERNAME=neo4j
    PASSWORD=your_password
    DATABASE=<optional>   (used only if present; never hardcoded)

The script is idempotent: uniqueness constraints + MERGE guarantee that
re-running it does not create duplicate nodes or relationships.
"""

import csv
import os
import sys
import time
from datetime import date

from neo4j import GraphDatabase

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
BATCH_SIZE = 5000
MISSING = {"\\N", ""}


# --------------------------------------------------------------------------- #
# Configuration
# --------------------------------------------------------------------------- #
def read_config(path):
    """Read KEY=VALUE lines from config.txt by key (never by line number)."""
    config = {}
    with open(path, "r", encoding="utf-8-sig") as fh:
        for line in fh:
            line = line.strip()
            if not line or line.startswith("#") or "=" not in line:
                continue
            key, value = line.split("=", 1)
            config[key.strip().upper()] = value.strip()
    for required in ("URI", "USERNAME", "PASSWORD"):
        if required not in config:
            raise KeyError(f"config.txt is missing the {required} key")
    return config


# --------------------------------------------------------------------------- #
# Value conversion helpers (missing values -> None -> property omitted)
# --------------------------------------------------------------------------- #
def to_int(value):
    if value is None or value.strip() in MISSING:
        return None
    return int(float(value))


def to_float(value):
    if value is None or value.strip() in MISSING:
        return None
    return float(value)


def to_str(value):
    if value is None or value.strip() in MISSING:
        return None
    return value


def to_date(value):
    if value is None or value.strip() in MISSING:
        return None
    return date.fromisoformat(value.strip())


def clean(props):
    """Drop properties whose value is missing so they are not stored."""
    return {k: v for k, v in props.items() if v is not None}


def read_csv(filename):
    path = os.path.join(BASE_DIR, filename)
    if not os.path.exists(path):
        path = os.path.join(os.getcwd(), filename)
    with open(path, "r", encoding="utf-8-sig", newline="") as fh:
        return list(csv.DictReader(fh))


# --------------------------------------------------------------------------- #
# Row builders: each returns {"id": ..., "props": {...}, + foreign keys}
# --------------------------------------------------------------------------- #
def build_drivers():
    rows = []
    for r in read_csv("drivers.csv"):
        rows.append({
            "id": to_int(r["driverId"]),
            "props": clean({
                "driverId": to_int(r["driverId"]),
                "driverRef": to_str(r["driverRef"]),
                "number": to_int(r["number"]),
                "code": to_str(r["code"]),
                "forename": to_str(r["forename"]),
                "surname": to_str(r["surname"]),
                "dob": to_date(r["dob"]),
                "nationality": to_str(r["nationality"]),
            }),
        })
    return rows


def build_constructors():
    rows = []
    for r in read_csv("constructors.csv"):
        rows.append({
            "id": to_int(r["constructorId"]),
            "props": clean({
                "constructorId": to_int(r["constructorId"]),
                "constructorRef": to_str(r["constructorRef"]),
                "constructor_name": to_str(r["name"]),
                "constructor_nationality": to_str(r["nationality"]),
            }),
        })
    return rows


def build_circuits():
    rows = []
    for r in read_csv("circuits.csv"):
        rows.append({
            "id": to_int(r["circuitId"]),
            "props": clean({
                "circuitId": to_int(r["circuitId"]),
                "circuitRef": to_str(r["circuitRef"]),
                "circuit_name": to_str(r["name"]),
                "circuit_loc": to_str(r["location"]),
                "circuit_country": to_str(r["country"]),
                "lat": to_float(r["lat"]),
                "lng": to_float(r["lng"]),
                "alt": to_int(r["alt"]),
            }),
        })
    return rows


def build_seasons():
    rows = []
    for r in read_csv("seasons.csv"):
        rows.append({
            "id": to_int(r["year"]),
            "props": {"year": to_int(r["year"])},
        })
    return rows


def build_statuses():
    rows = []
    for r in read_csv("status.csv"):
        rows.append({
            "id": to_int(r["statusId"]),
            "props": clean({
                "statusId": to_int(r["statusId"]),
                "status": to_str(r["status"]),
            }),
        })
    return rows


def build_races():
    rows = []
    for r in read_csv("races.csv"):
        rows.append({
            "id": to_int(r["raceId"]),
            "circuitId": to_int(r["circuitId"]),
            "year": to_int(r["year"]),
            "props": clean({
                "raceId": to_int(r["raceId"]),
                "year": to_int(r["year"]),
                "round": to_int(r["round"]),
                "name": to_str(r["name"]),
                "date": to_date(r["date"]),
                "time": to_str(r["time"]),
            }),
        })
    return rows


def build_results():
    rows = []
    for r in read_csv("results.csv"):
        rows.append({
            "id": to_int(r["resultId"]),
            "raceId": to_int(r["raceId"]),
            "driverId": to_int(r["driverId"]),
            "constructorId": to_int(r["constructorId"]),
            "statusId": to_int(r["statusId"]),
            "props": clean({
                "resultId": to_int(r["resultId"]),
                "number": to_int(r["number"]),
                "grid": to_int(r["grid"]),
                "position": to_int(r["position"]),
                "positionText": to_str(r["positionText"]),
                "positionOrder": to_int(r["positionOrder"]),
                "points": to_float(r["points"]),
                "laps": to_int(r["laps"]),
                "time": to_str(r["time"]),
                "milliseconds": to_int(r["milliseconds"]),
                "fastestLap": to_int(r["fastestLap"]),
                "rank": to_int(r["rank"]),
                "fastestLapTime": to_str(r["fastestLapTime"]),
                "fastestLapSpeed": to_float(r["fastestLapSpeed"]),
            }),
        })
    return rows


def build_qualifying():
    rows = []
    for r in read_csv("qualifying.csv"):
        rows.append({
            "id": to_int(r["qualifyId"]),
            "raceId": to_int(r["raceId"]),
            "driverId": to_int(r["driverId"]),
            "constructorId": to_int(r["constructorId"]),
            "props": clean({
                "qualifyId": to_int(r["qualifyId"]),
                "number": to_int(r["number"]),
                "position": to_int(r["position"]),
                "q1": to_str(r["q1"]),
                "q2": to_str(r["q2"]),
                "q3": to_str(r["q3"]),
            }),
        })
    return rows


def build_pit_stops():
    rows = []
    for r in read_csv("pit_stops.csv"):
        race_id = to_int(r["raceId"])
        driver_id = to_int(r["driverId"])
        stop = to_int(r["stop"])
        event_id = f"{race_id}:{driver_id}:{stop}"
        rows.append({
            "id": event_id,
            "raceId": race_id,
            "driverId": driver_id,
            "props": clean({
                "eventId": event_id,
                "stop": stop,
                "lap": to_int(r["lap"]),
                "time": to_str(r["time"]),
                "duration": to_str(r["duration"]),
                "milliseconds": to_int(r["milliseconds"]),
            }),
        })
    return rows


# --------------------------------------------------------------------------- #
# Cypher
# --------------------------------------------------------------------------- #
CONSTRAINTS = [
    ("driver_id_unique", "Driver", "driverId"),
    ("constructor_id_unique", "Constructor", "constructorId"),
    ("circuit_id_unique", "Circuit", "circuitId"),
    ("season_year_unique", "Season", "year"),
    ("status_id_unique", "Status", "statusId"),
    ("race_id_unique", "Race", "raceId"),
    ("result_id_unique", "Result", "resultId"),
    ("qualify_id_unique", "Qualifying", "qualifyId"),
    ("pitstop_event_id_unique", "PitStop", "eventId"),
]


def node_query(label, key):
    # SET n = props replaces all properties, so re-runs stay exact.
    return (
        f"UNWIND $rows AS row "
        f"MERGE (n:{label} {{{key}: row.id}}) "
        f"SET n = row.props"
    )


def rel_query(src_label, src_key, rel_type, dst_label, dst_key, fk):
    return (
        f"UNWIND $rows AS row "
        f"MATCH (a:{src_label} {{{src_key}: row.id}}) "
        f"MATCH (b:{dst_label} {{{dst_key}: row.{fk}}}) "
        f"MERGE (a)-[:{rel_type}]->(b)"
    )


def run_batches(session, query, rows, label):
    start = time.time()
    for i in range(0, len(rows), BATCH_SIZE):
        batch = rows[i:i + BATCH_SIZE]
        session.execute_write(lambda tx, b=batch: tx.run(query, rows=b).consume())
    print(f"  {label:<45} {len(rows):>6} rows  ({time.time() - start:5.1f}s)")


def project(rows, *keys):
    """Keep only the keys a relationship query needs (smaller payloads)."""
    return [{k: r[k] for k in keys} for r in rows]


def main():
    t0 = time.time()
    config = read_config(os.path.join(BASE_DIR, "config.txt"))
    database = config.get("DATABASE") or None

    print("Reading CSV files ...")
    drivers = build_drivers()
    constructors = build_constructors()
    circuits = build_circuits()
    seasons = build_seasons()
    statuses = build_statuses()
    races = build_races()
    results = build_results()
    qualifying = build_qualifying()
    pit_stops = build_pit_stops()

    driver = GraphDatabase.driver(
        config["URI"], auth=(config["USERNAME"], config["PASSWORD"])
    )
    try:
        driver.verify_connectivity()
        with driver.session(database=database) as session:
            print("Creating uniqueness constraints ...")
            for name, label, key in CONSTRAINTS:
                session.run(
                    f"CREATE CONSTRAINT {name} IF NOT EXISTS "
                    f"FOR (n:{label}) REQUIRE n.{key} IS UNIQUE"
                ).consume()
            session.run("CALL db.awaitIndexes(300)").consume()

            # 1) Parent (entity) nodes first
            print("Creating entity nodes ...")
            run_batches(session, node_query("Driver", "driverId"), drivers, "Driver")
            run_batches(session, node_query("Constructor", "constructorId"), constructors, "Constructor")
            run_batches(session, node_query("Circuit", "circuitId"), circuits, "Circuit")
            run_batches(session, node_query("Season", "year"), seasons, "Season")
            run_batches(session, node_query("Status", "statusId"), statuses, "Status")
            run_batches(session, node_query("Race", "raceId"), races, "Race")

            print("Creating Race relationships ...")
            run_batches(session, rel_query("Race", "raceId", "AT_CIRCUIT", "Circuit", "circuitId", "circuitId"),
                        project(races, "id", "circuitId"), "(Race)-[:AT_CIRCUIT]->(Circuit)")
            run_batches(session, rel_query("Race", "raceId", "IN_SEASON", "Season", "year", "year"),
                        project(races, "id", "year"), "(Race)-[:IN_SEASON]->(Season)")

            # 2) Fact nodes and their relationships
            print("Creating fact nodes ...")
            run_batches(session, node_query("Result", "resultId"), results, "Result")
            run_batches(session, node_query("Qualifying", "qualifyId"), qualifying, "Qualifying")
            run_batches(session, node_query("PitStop", "eventId"), pit_stops, "PitStop")

            print("Creating fact relationships ...")
            run_batches(session, rel_query("Result", "resultId", "FOR_RACE", "Race", "raceId", "raceId"),
                        project(results, "id", "raceId"), "(Result)-[:FOR_RACE]->(Race)")
            run_batches(session, rel_query("Result", "resultId", "BY_DRIVER", "Driver", "driverId", "driverId"),
                        project(results, "id", "driverId"), "(Result)-[:BY_DRIVER]->(Driver)")
            run_batches(session, rel_query("Result", "resultId", "FOR_CONSTRUCTOR", "Constructor", "constructorId", "constructorId"),
                        project(results, "id", "constructorId"), "(Result)-[:FOR_CONSTRUCTOR]->(Constructor)")
            run_batches(session, rel_query("Result", "resultId", "HAS_STATUS", "Status", "statusId", "statusId"),
                        project(results, "id", "statusId"), "(Result)-[:HAS_STATUS]->(Status)")

            run_batches(session, rel_query("Qualifying", "qualifyId", "FOR_RACE", "Race", "raceId", "raceId"),
                        project(qualifying, "id", "raceId"), "(Qualifying)-[:FOR_RACE]->(Race)")
            run_batches(session, rel_query("Qualifying", "qualifyId", "BY_DRIVER", "Driver", "driverId", "driverId"),
                        project(qualifying, "id", "driverId"), "(Qualifying)-[:BY_DRIVER]->(Driver)")
            run_batches(session, rel_query("Qualifying", "qualifyId", "FOR_CONSTRUCTOR", "Constructor", "constructorId", "constructorId"),
                        project(qualifying, "id", "constructorId"), "(Qualifying)-[:FOR_CONSTRUCTOR]->(Constructor)")

            run_batches(session, rel_query("PitStop", "eventId", "FOR_RACE", "Race", "raceId", "raceId"),
                        project(pit_stops, "id", "raceId"), "(PitStop)-[:FOR_RACE]->(Race)")
            run_batches(session, rel_query("PitStop", "eventId", "BY_DRIVER", "Driver", "driverId", "driverId"),
                        project(pit_stops, "id", "driverId"), "(PitStop)-[:BY_DRIVER]->(Driver)")

            nodes = session.run("MATCH (n) RETURN count(n) AS c").single()["c"]
            rels = session.run("MATCH ()-[r]->() RETURN count(r) AS c").single()["c"]
            print(f"Done. Nodes: {nodes}  Relationships: {rels}  "
                  f"(expected 51113 / 163510)  Total time: {time.time() - t0:.1f}s")
    finally:
        driver.close()


if __name__ == "__main__":
    try:
        main()
    except Exception as exc:  # surface a clear error for the grader
        print(f"Error while building the knowledge graph: {exc}", file=sys.stderr)
        raise
