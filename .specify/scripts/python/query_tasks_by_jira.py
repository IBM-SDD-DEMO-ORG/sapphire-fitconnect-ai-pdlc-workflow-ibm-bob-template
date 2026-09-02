#!/usr/bin/env python3
"""
Query a Bob SQLite DB for all tasks whose first_message contains a JIRA story ID.

Usage:
    python query_tasks_by_jira.py <db_path> <jira_id> <project_id>

Arguments:
    db_path     Path to the sqlite file (e.g. C:/Users/.../.bob/db/bob.db)
    jira_id     The Jira story ID to search for (e.g. DPDE-225). Used in a
                LIKE '%<jira_id>%' search against the first_message column.
    project_id  The project_id value to scope the search to this workspace.

Output:
    JSON written to .specify/tmp/bob_tasks_<jira_id>.json (path printed to stdout).
    The JSON is an array of task objects, each containing:
      - task_id       : the task id
      - first_message : the first_message value (used by agent to infer workflow phase)
      - created_at    : ISO timestamp of task creation
      - costs         : parsed costs object (or null)
"""

import argparse
import io
import json
import os
import sqlite3
import sys

# Ensure stdout/stderr emit UTF-8 regardless of the terminal's default encoding.
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")
sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding="utf-8", errors="replace")


def parse_args():
    parser = argparse.ArgumentParser(
        description="Query Bob SQLite DB for all tasks matching a Jira story ID."
    )
    parser.add_argument("db_path", help="Path to the sqlite file")
    parser.add_argument("jira_id", help="The Jira story ID to match (LIKE search)")
    parser.add_argument("project_id", help="The project_id to scope the search")
    return parser.parse_args()


def main():
    args = parse_args()

    try:
        conn = sqlite3.connect(args.db_path)
    except sqlite3.OperationalError as e:
        print(json.dumps({"error": f"Cannot open database: {e}"}), file=sys.stderr)
        sys.exit(1)

    conn.row_factory = sqlite3.Row
    c = conn.cursor()

    # LIKE search: any task whose first_message mentions the JIRA id
    like_pattern = f"%{args.jira_id}%"
    c.execute(
        """
        SELECT id, first_message, created_at, costs
        FROM tasks
        WHERE first_message LIKE ? AND project_id = ?
        ORDER BY created_at ASC
        """,
        (like_pattern, args.project_id),
    )
    rows = c.fetchall()
    conn.close()

    if not rows:
        print(
            json.dumps(
                {"error": f"No tasks found matching JIRA id '{args.jira_id}' in project '{args.project_id}'"}
            ),
            file=sys.stderr,
        )
        sys.exit(1)

    tasks = []
    for row in rows:
        raw_costs = row["costs"]
        costs = None
        if raw_costs is not None:
            try:
                costs = json.loads(raw_costs)
            except json.JSONDecodeError:
                costs = raw_costs  # return raw string if unparseable

        tasks.append(
            {
                "task_id": row["id"],
                "first_message": row["first_message"],
                "created_at": row["created_at"],
                "costs": costs,
            }
        )

    # Resolve .specify/tmp/ relative to this script (scripts/python/ -> .specify/tmp/)
    script_dir = os.path.dirname(os.path.abspath(__file__))
    tmp_dir = os.path.normpath(os.path.join(script_dir, "..", "..", "tmp"))
    os.makedirs(tmp_dir, exist_ok=True)

    safe_id = args.jira_id.replace("/", "_").replace("\\", "_")
    out_path = os.path.join(tmp_dir, f"bob_tasks_{safe_id}.json")
    with open(out_path, "w", encoding="utf-8") as f:
        json.dump(tasks, f, ensure_ascii=False, indent=2)

    # Print only the file path so callers can easily consume it.
    print(out_path)


if __name__ == "__main__":
    main()
