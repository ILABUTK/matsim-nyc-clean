#!/usr/bin/env python3
"""Build a link-volume map and hourly loading chart from a MATSim output run."""
import argparse
import gzip
from collections import Counter
from pathlib import Path

import geopandas as gpd
import matplotlib.pyplot as plt
import pandas as pd
from lxml import etree
from shapely.geometry import LineString

SOURCE_CRS = "EPSG:3628"


def parse_network(network_path):
    nodes = {}
    links = []
    context = etree.iterparse(gzip.open(network_path, "rb"), events=("end",), tag=("node", "link"))
    for _, elem in context:
        if elem.tag == "node":
            nodes[elem.get("id")] = (float(elem.get("x")), float(elem.get("y")))
        else:
            links.append({
                "link_id": elem.get("id"),
                "from_node": elem.get("from"),
                "to_node": elem.get("to"),
                "length_m": float(elem.get("length")),
                "freespeed": float(elem.get("freespeed")),
                "capacity": float(elem.get("capacity")),
                "modes": elem.get("modes"),
            })
        elem.clear()
    return nodes, links


def build_link_geodataframe(nodes, links):
    df = pd.DataFrame(links)
    geometry = [
        LineString([nodes[row.from_node], nodes[row.to_node]])
        for row in df.itertuples()
    ]
    return gpd.GeoDataFrame(df, geometry=geometry, crs=SOURCE_CRS)


def count_link_volumes(events_path):
    total = Counter()
    by_hour = Counter()
    context = etree.iterparse(gzip.open(events_path, "rb"), events=("end",), tag="event")
    for _, elem in context:
        if elem.get("type") == "entered link":
            link_id = elem.get("link")
            total[link_id] += 1
            hour = int(float(elem.get("time")) // 3600) % 24
            by_hour[hour] += 1
        elem.attrib.clear()
        elem.clear()
    return total, by_hour


def plot_static_map(gdf, out_path, title):
    used = gdf[gdf["volume"] > 0].sort_values("volume")
    fig, ax = plt.subplots(figsize=(10, 12))
    gdf.plot(ax=ax, color="#dddddd", linewidth=0.15)
    used.plot(ax=ax, column="volume", cmap="plasma", linewidth=used["volume"].clip(upper=20) / 4,
              legend=True, legend_kwds={"label": "vehicles entering link (whole sim)"})
    ax.set_title(title)
    ax.set_axis_off()
    fig.tight_layout()
    fig.savefig(out_path, dpi=200)
    plt.close(fig)


def plot_hourly_loading(by_hour, out_path):
    hours = list(range(24))
    counts = [by_hour.get(h, 0) for h in hours]
    fig, ax = plt.subplots(figsize=(9, 4))
    ax.bar(hours, counts, color="#3366cc")
    ax.set_xlabel("hour of day")
    ax.set_ylabel("link-entry events")
    ax.set_title("Network loading by hour")
    ax.set_xticks(hours)
    fig.tight_layout()
    fig.savefig(out_path, dpi=200)
    plt.close(fig)


def plot_interactive_map(gdf, out_path):
    used = gdf[gdf["volume"] > 0].to_crs(4326)
    m = used.explore(
        column="volume",
        cmap="plasma",
        tooltip=["link_id", "volume", "modes", "freespeed"],
        tiles="CartoDB positron",
    )
    m.save(out_path)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("run_dir", type=Path, help="MATSim output directory, e.g. output/bqx-8mph-newparams")
    parser.add_argument("--prefix", default="BUILT", help="output file prefix used in the run (runId)")
    parser.add_argument("--out", type=Path, default=Path("analysis/output"))
    args = parser.parse_args()

    args.out.mkdir(parents=True, exist_ok=True)
    network_path = args.run_dir / f"{args.prefix}.output_network.xml.gz"
    events_path = args.run_dir / f"{args.prefix}.output_events.xml.gz"

    print(f"parsing network: {network_path}")
    nodes, links = parse_network(network_path)
    gdf = build_link_geodataframe(nodes, links)

    print(f"counting link volumes: {events_path}")
    volumes, by_hour = count_link_volumes(events_path)
    gdf["volume"] = gdf["link_id"].map(volumes).fillna(0).astype(int)

    print("writing GeoJSON")
    gdf.to_file(args.out / "link_volumes.geojson", driver="GeoJSON")

    print("writing static map")
    plot_static_map(gdf, args.out / "link_volume_map.png", f"Link volumes — {args.run_dir.name}")

    print("writing hourly loading chart")
    plot_hourly_loading(by_hour, args.out / "hourly_loading.png")

    print("writing interactive map")
    plot_interactive_map(gdf, args.out / "link_volume_map.html")

    print(f"done. {int(gdf['volume'].gt(0).sum())} / {len(gdf)} links used, "
          f"total entries: {sum(volumes.values())}")


if __name__ == "__main__":
    main()
