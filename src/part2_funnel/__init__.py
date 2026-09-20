"""Part 2 — progression funnel (ARCHITECTURE.md §10.6).

SQL does every aggregation (§7.3). This package executes nothing against
BigQuery: it reads the already-aggregated query results committed under
outputs/tables/part2_q*.csv, computes the closed-form Wilson intervals §10.6.4
requires, applies the n<30 suppression rule in one place (A-163), emits every
derived figure as its own committed cell (§7.5, A-158, A-165), renders the report
tables and figures, and verifies and audits what it wrote.
"""
