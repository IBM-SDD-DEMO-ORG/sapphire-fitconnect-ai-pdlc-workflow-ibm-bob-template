#!/usr/bin/env python3
"""
Query a Bob sqlite DB for a task and its messages.

Usage:
    python query_task.py <db_path> <first_message> <project_id>

Arguments:
    db_path        Path to the sqlite file (e.g. C:/Users/.../.bob/db/bob.db)
    first_message  The first_message value to match in the tasks table
    project_id     The project_id value to match in the tasks table

Output:
    JSON written to .specify/tmp/bob_task_<id>.json (path printed to stdout) containing:
      - task_id   : the matched task id
      - costs     : parsed costs object (or null)
      - messages  : array of {role, data} objects from the messages table
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
        description="Query Bob sqlite DB for a task and its messages."
    )
    parser.add_argument("db_path", help="Path to the sqlite file")
    parser.add_argument("first_message", help="The first_message to match in tasks")
    parser.add_argument("project_id", help="The project_id to match in tasks")
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

    # --- 1. Find the task ---
    c.execute(
        """
        SELECT id, costs
        FROM tasks
        WHERE first_message = ? AND project_id = ?
        ORDER BY created_at DESC
        LIMIT 1
        """,
        (args.first_message, args.project_id),
    )
    task_row = c.fetchone()

    if task_row is None:
        print(
            json.dumps(
                {
                    "error": "No task found matching the given first_message and project_id"
                }
            ),
            file=sys.stderr,
        )
        conn.close()
        sys.exit(1)

    task_id = task_row["id"]
    raw_costs = task_row["costs"]

    # Parse costs JSON if present
    costs = None
    if raw_costs is not None:
        try:
            costs = json.loads(raw_costs)
        except json.JSONDecodeError:
            costs = raw_costs  # return raw string if it can't be parsed

    # --- 2. Fetch messages for this task ---
    c.execute(
        """
        SELECT role, data
        FROM messages
        WHERE task_id = ?
        ORDER BY created_at ASC
        """,
        (task_id,),
    )
    message_rows = c.fetchall()
    conn.close()

    messages = []
    for row in message_rows:
        # data is stored as a JSON string; parse it so the output is clean JSON
        raw_data = row["data"]
        try:
            parsed_data = json.loads(raw_data)
        except (json.JSONDecodeError, TypeError):
            parsed_data = raw_data  # keep as-is if not valid JSON

        messages.append({"role": row["role"], "data": parsed_data})

    result = {
        "task_id": task_id,
        "costs": costs,
        "messages": messages,
    }

    # Resolve .specify/tmp/ relative to this script's location, then two levels up
    # (scripts/python/ -> scripts/ -> .specify/).
    script_dir = os.path.dirname(os.path.abspath(__file__))
    tmp_dir = os.path.normpath(os.path.join(script_dir, "..", "..", "tmp"))
    os.makedirs(tmp_dir, exist_ok=True)

    out_path = os.path.join(tmp_dir, f"bob_task_{task_id}.json")
    with open(out_path, "w", encoding="utf-8") as f:
        json.dump(result, f, ensure_ascii=False, indent=2)

    # Print only the file path so callers can easily consume it.
    print(out_path)


if __name__ == "__main__":
    main()
