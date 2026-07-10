#!/usr/bin/env python3
"""Deterministically sample a fixed number of persons from a MATSim population file."""
import argparse
import random
from pathlib import Path

from lxml import etree

DOCTYPE = b'<!DOCTYPE population SYSTEM "http://www.matsim.org/files/dtd/population_v5.dtd">'


def sample(source, count, seed):
    tree = etree.parse(str(source))
    persons = tree.getroot().findall("person")
    rng = random.Random(seed)
    sampled = rng.sample(persons, count)
    sampled.sort(key=lambda p: int(p.get("id")))
    return persons, sampled


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("source", type=Path, help="full population file, e.g. input/final_population.xml")
    parser.add_argument("dest", type=Path, help="output population file")
    parser.add_argument("-n", "--count", type=int, default=3893, help="number of persons to keep")
    parser.add_argument("--seed", type=int, default=42, help="RNG seed, for a reproducible sample")
    args = parser.parse_args()

    all_persons, sampled = sample(args.source, args.count, args.seed)

    new_root = etree.Element("population")
    for person in sampled:
        new_root.append(person)

    args.dest.write_bytes(
        b'<?xml version="1.0" encoding="UTF-8"?>\n' + DOCTYPE + b"\n"
        + etree.tostring(new_root, pretty_print=True)
    )
    print(f"sampled {len(sampled)} / {len(all_persons)} persons (seed={args.seed}) -> {args.dest}")


if __name__ == "__main__":
    main()
