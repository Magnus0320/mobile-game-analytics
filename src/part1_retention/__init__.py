"""Part 1 — retention and install cohorts (ARCHITECTURE.md §10.5).

SQL does every aggregation (§7.3). This package executes nothing against
BigQuery: it reads the already-aggregated query results committed under
outputs/tables/part1_q*.csv, computes the closed-form Wilson intervals §10.5.3
requires, applies the n<30 suppression rule in one place (A-139), renders the
report tables and figures, and verifies what it wrote.
"""
