#!/usr/bin/env python3
import argparse, subprocess, yaml, os

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--cluster", required=True)
    parser.add_argument("--region", required=True)
    args = parser.parse_args()

    # Configure kubectl for the EKS cluster
    subprocess.run([
        "aws", "eks", "update-kubeconfig",
        "--name", args.cluster,
        "--region", args.region
    ], check=True)

    with open("charts.yaml") as f:
        charts = yaml.safe_load(f)

    for chart in charts.get("charts", []):
        release = chart["name"]
        repo = chart["repo"]
        version = chart.get("version")
        values = chart.get("values")

        subprocess.run(["helm", "repo", "add", release, repo], check=True)
        cmd = ["helm", "upgrade", "--install", release, f"{release}/{release}"]
        if version:
            cmd += ["--version", version]
        if values:
            cmd += ["-f", values]
        subprocess.run(cmd, check=True)

if __name__ == "__main__":
    main()
