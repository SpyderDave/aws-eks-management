#!/usr/bin/env python3
import os, subprocess, yaml, json

REGION = os.environ.get("AWS_REGION", "ca-central-1")

def list_clusters():
    out = subprocess.check_output(["aws", "eks", "list-clusters", "--region", REGION])
    return json.loads(out)["clusters"]

def main():
    with open("charts.yaml") as f:
        charts = yaml.safe_load(f)

    clusters = list_clusters()
    for cluster in clusters:
        subprocess.run([
            "aws", "eks", "update-kubeconfig",
            "--name", cluster, "--region", REGION
        ], check=True)

        for chart in charts.get("charts", []):
            release = chart["name"]
            repo = chart["repo"]
            version = chart.get("version")

            print(f"Auditing {release} on cluster {cluster}...")
            result = subprocess.run(["helm", "status", release], capture_output=True, text=True)
            if result.returncode != 0:
                print(f"{release} missing, reinstalling...")
                subprocess.run(["helm", "repo", "add", release, repo], check=True)
                cmd = ["helm", "upgrade", "--install", release, f"{release}/{release}"]
                if version:
                    cmd += ["--version", version]
                subprocess.run(cmd, check=True)

if __name__ == "__main__":
    main()
