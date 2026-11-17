"""
Helper (NOT part of the submission): verifies the KG and runs queries.txt
exactly the way an autograder would extract them ("//N. Query N" blocks).

Usage:  python test_queries.py
"""
import os
import re
import sys

from neo4j import GraphDatabase

from Create_kg import read_config

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")

cfg = read_config(os.path.join(BASE_DIR, "config.txt"))
db = cfg.get("DATABASE") or None

with GraphDatabase.driver(cfg["URI"], auth=(cfg["USERNAME"], cfg["PASSWORD"])) as driver:
    nodes = driver.execute_query("MATCH (n) RETURN count(n) AS c", database_=db).records[0]["c"]
    rels = driver.execute_query("MATCH ()-[r]->() RETURN count(r) AS c", database_=db).records[0]["c"]
    print(f"Nodes: {nodes} (expected 51113)   Relationships: {rels} (expected 163510)")

    with open(os.path.join(BASE_DIR, "queries.txt"), encoding="utf-8") as fh:
        text = fh.read()
    parts = re.split(r"//\s*(\d+)\.\s*Query\s*\d+", text)
    for i in range(1, len(parts), 2):
        num, query = parts[i], parts[i + 1].strip()
        records, _, keys = driver.execute_query(query, database_=db)
        print(f"\n=== Query {num}: {len(records)} rows, columns {keys}")
        for rec in records[:15]:
            print("  ", dict(rec))
