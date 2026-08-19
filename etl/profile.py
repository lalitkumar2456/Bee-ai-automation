from __future__ import annotations
import csv
from pathlib import Path

def profile(path: Path) -> dict:
    with path.open(encoding='utf-8-sig', newline='') as f: rows = list(csv.DictReader(f))
    columns = list(rows[0]) if rows else []
    nulls = {col: sum(not (row.get(col) or '').strip() for row in rows) for col in columns}
    duplicate_count = len(rows) - len({tuple(row.get(c, '') for c in columns) for row in rows})
    return {'file':path.name, 'rows':len(rows), 'columns':columns, 'nulls':nulls, 'exact_duplicates':duplicate_count}

if __name__ == '__main__':
    data = Path(__file__).resolve().parents[1] / 'data'
    files = list(data.glob('*.csv'))
    if not files: print('No CSV files found. Add the three source CSVs to data/.')
    for path in files:
        report = profile(path)
        print(f"\n{report['file']}: {report['rows']} rows\nColumns: {', '.join(report['columns'])}\nExact duplicate rows: {report['exact_duplicates']}\nNull values: {report['nulls']}")
