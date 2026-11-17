# Milestone 2: Formula 1 Knowledge Graph

## Submission files
| File | Purpose |
|------|---------|
| `Create_kg.py` | Builds the KG in Neo4j from the CSVs in the same folder (uses `config.txt`) |
| `config.txt` | Neo4j credentials (`URI`, `USERNAME`, `PASSWORD`, optional `DATABASE`), read by key |
| `queries.txt` | Cypher queries 1–5 in the `//N. Query N` format (UTF-8) |

`test_queries.py` is only a local helper for testing. Do not submit it.

## How to test
1. Start a Neo4j 5 database, using either **Neo4j Desktop** (create a local DBMS and start it) or **Docker**:
   ```bash
   docker run -d --name neo4j-ms2 -p 7474:7474 -p 7687:7687 -e NEO4J_AUTH=neo4j/ms2testpass neo4j:5
   ```
2. Put your password in `config.txt` (Docker example: `PASSWORD=ms2testpass`).
3. Install the driver and build the graph (about 20 s locally; the limit is 30 min):
   ```bash
   pip install neo4j
   python Create_kg.py
   ```
   The last line should read `Nodes: 51113  Relationships: 163510`. Run it again to confirm the counts don't change (no duplicates).
4. Run the queries:
   ```bash
   python test_queries.py
   ```
   You can also paste each query into Neo4j Browser at http://localhost:7474.

## Expected results (sanity check)
- Q1: Max Verstappen 388.5 pts, 10 wins; Lewis Hamilton 385.5 pts, 8 wins …
- Q2: Mercedes 320 entries, 298 classified, 0.93125 …
- Q3: Mercedes, 100 shared races, Hamilton ahead 75, Bottas ahead 25
- Q4: Ayrton Senna 10 starts, avg 3.8, 6 wins; Lewis Hamilton 13 starts, avg 4.0, 3 wins …
- Q5: 6 drivers: Ocon, Pérez, Ricciardo, Sainz, Stroll, Vettel
