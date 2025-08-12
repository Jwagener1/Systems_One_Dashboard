"""Utility script to discover InfluxDB schema elements.

Reads environment variables for connection (see .env.example) and prints:
 - Measurements in the bucket
 - Tag keys (within a time range)
 - Field keys (within a time range)
 - (Optionally) tag values for a specific tag key

Usage (PowerShell example):
    $env:INFLUXDB_URL="https://influxdb.example.com"
    $env:INFLUXDB_TOKEN="<TOKEN>"
    $env:INFLUXDB_ORG="my-org"
    $env:INFLUXDB_BUCKET="telemetry"
    python scripts/discover_influx.py --range -7d --tag-values deviceType

The script purposefully avoids any application internals so it can be run
stand‑alone for exploration.
"""

from __future__ import annotations

import os
import argparse
from pathlib import Path
from typing import List, Any, cast
import pandas as pd

# Auto-load a .env file if present for convenience
try:  # pragma: no cover - optional
    from dotenv import load_dotenv  # type: ignore

    # Find project root and load .env explicitly
    project_root = Path(__file__).resolve().parent.parent
    env_file = project_root / ".env"
    if env_file.exists():
        load_dotenv(env_file, override=True)
    else:
        # Fallback: load from current directory
        load_dotenv()
except Exception:  # pragma: no cover
    pass

try:
    from influxdb_client import InfluxDBClient  # type: ignore
except Exception as exc:  # pragma: no cover
    raise SystemExit(
        "influxdb-client is required. Install with 'pip install influxdb-client'."
    ) from exc


def env(name: str, required: bool = True, default: str | None = None) -> str:
    val = os.environ.get(name, default)
    if required and (val is None or val == ""):
        raise SystemExit(
            f"Missing required environment variable: {name}\n"
            f"Checked current process environment and .env at: {Path.cwd() / '.env'}"
        )
    return val or ""


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Discover InfluxDB schema")
    parser.add_argument(
        "--range",
        dest="range_start",
        default=os.environ.get("INFLUXDB_RANGE_START", "-1h"),
        help="Time range start (Flux duration, e.g. -1h, -24h, -7d)",
    )
    parser.add_argument(
        "--tag-values", dest="tag_values", help="Optional tag key to list values for"
    )
    parser.add_argument(
        "--limit", type=int, default=50, help="Limit for tag values listing"
    )
    parser.add_argument(
        "--measurement-sample",
        dest="measurement_sample",
        help="Measurement name to pull a sample dataframe for",
    )
    parser.add_argument(
        "--sample-limit",
        dest="sample_limit",
        type=int,
        default=25,
        help="Row limit for measurement sample",
    )
    parser.add_argument(
        "--export-csv",
        dest="export_csv",
        help="Optional path to export sampled measurement as CSV",
    )
    parser.add_argument(
        "--print-env",
        dest="print_env",
        action="store_true",
        help="Print the resolved InfluxDB-related environment variables (token masked)",
    )
    return parser.parse_args()


def run_flux(client: Any, org: str, flux: str) -> List[str]:
    """Execute a Flux query and return a list of _value entries (deduped)."""
    tables = client.query_api().query(flux, org=org)  # type: ignore[attr-defined]
    results: List[str] = []
    for table in tables:  # type: ignore
        for record in table.records:  # type: ignore[attr-defined]
            if hasattr(record, "get_value"):
                try:  # pragma: no cover - defensive
                    results.append(record.get_value())  # type: ignore[attr-defined]
                except Exception:  # pragma: no cover
                    pass
    seen: set[str] = set()
    deduped: List[str] = []
    for r in results:
        if r not in seen:
            seen.add(r)
            deduped.append(r)
    return deduped


def main() -> None:
    args = parse_args()
    url = env("INFLUXDB_URL")
    token = env("INFLUXDB_TOKEN")
    org = env("INFLUXDB_ORG")
    bucket = env("INFLUXDB_BUCKET")

    if args.print_env:

        def mask(v: str) -> str:
            if len(v) <= 8:
                return "***" if v else "<empty>"
            return v[:4] + "..." + v[-4:]

        print("Resolved environment variables:")
        print(f"  INFLUXDB_URL={url}")
        print(f"  INFLUXDB_ORG={org}")
        print(f"  INFLUXDB_BUCKET={bucket}")
        print(f"  INFLUXDB_RANGE_START={os.environ.get('INFLUXDB_RANGE_START', '')}")
        print(f"  INFLUXDB_MEASUREMENT={os.environ.get('INFLUXDB_MEASUREMENT', '')}")
        print(f"  INFLUXDB_CATEGORY_TAG={os.environ.get('INFLUXDB_CATEGORY_TAG', '')}")
        print(f"  INFLUXDB_VALUE1_FIELD={os.environ.get('INFLUXDB_VALUE1_FIELD', '')}")
        print(f"  INFLUXDB_VALUE2_FIELD={os.environ.get('INFLUXDB_VALUE2_FIELD', '')}")
        print(f"  INFLUXDB_TOKEN={mask(token)}")

    with InfluxDBClient(url=url, token=token, org=org, timeout=10_000) as client:  # type: ignore
        flux_measurements = f'import "influxdata/influxdb/schema"\nschema.measurements(bucket: "{bucket}")'
        measurements = run_flux(client, org, flux_measurements)

        flux_tag_keys = f'import "influxdata/influxdb/schema"\nschema.tagKeys(bucket: "{bucket}", start: {args.range_start})'
        tag_keys = run_flux(client, org, flux_tag_keys)

        flux_field_keys = f'import "influxdata/influxdb/schema"\nschema.fieldKeys(bucket: "{bucket}", start: {args.range_start})'
        field_keys = run_flux(client, org, flux_field_keys)

        print("\n=== InfluxDB Schema Discovery ===")
        print(f"Bucket: {bucket}  Range start: {args.range_start}")
        print("Measurements (candidates for INFLUXDB_MEASUREMENT):")
        for m in measurements:
            print(f"  - {m}")

        print("\nTag Keys (candidates for INFLUXDB_CATEGORY_TAG):")
        for t in tag_keys:
            print(f"  - {t}")

        print(
            "\nField Keys (candidates for INFLUXDB_VALUE1_FIELD / INFLUXDB_VALUE2_FIELD):"
        )
        for f in field_keys:
            print(f"  - {f}")

        if args.tag_values:
            flux_tag_values = (
                f'import "influxdata/influxdb/schema"\n'
                f'schema.tagValues(bucket: "{bucket}", tag: "{args.tag_values}", start: {args.range_start})'
            )
            tag_values = run_flux(client, org, flux_tag_values)[: args.limit]
            print(f"\nValues for tag '{args.tag_values}' (first {args.limit}):")
            for v in tag_values:
                print(f"  - {v}")

        # Optional measurement sample
        if args.measurement_sample:
            meas = args.measurement_sample
            flux_sample = f"""
from(bucket: "{bucket}")
  |> range(start: {args.range_start})
  |> filter(fn: (r) => r["_measurement"] == "{meas}")
  |> pivot(rowKey:["_time","_measurement"], columnKey:["_field"], valueColumn:"_value")
  |> sort(columns:["_time"], desc: true)
  |> limit(n:{args.sample_limit})
"""
            try:
                raw = client.query_api().query_data_frame(org=org, query=flux_sample)  # type: ignore[attr-defined]
                if isinstance(raw, list):
                    df_sample = pd.concat(
                        cast(List[pd.DataFrame], raw), ignore_index=True
                    )
                else:
                    df_sample = cast(pd.DataFrame, raw)
                print(
                    f"\nSample rows for measurement '{meas}' (limit {args.sample_limit}):"
                )
                # Separate internal columns (prefixed with '_')
                internal_cols = [
                    c
                    for c in df_sample.columns
                    if hasattr(c, "startswith") and str(c).startswith("_")
                ]
                df_display = df_sample.drop(columns=internal_cols, errors="ignore")
                print("Columns:")
                for c in df_display.columns:
                    print(f"  - {c}")
                print("\nPreview:")
                preview = df_display.head(min(10, args.sample_limit))
                try:
                    text_preview = preview.to_csv(index=False)
                except Exception:  # pragma: no cover
                    text_preview = str(preview)
                print(text_preview.strip())
                if args.export_csv:
                    df_display.to_csv(args.export_csv, index=False)
                    print(f"Exported sample to {args.export_csv}")
            except Exception as e:  # pragma: no cover
                print(f"Failed to sample measurement '{meas}': {e}")

        print("\nSet the chosen values as environment variables and run the app.")


if __name__ == "__main__":  # pragma: no cover
    main()
