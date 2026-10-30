#!/usr/bin/env python3
import boto3
import time
import argparse
import sys

def wait_for_eks_cluster(cluster_name, region, timeout, poll_interval):
    """
    Wait for an EKS cluster to become ACTIVE.
    """
    client = boto3.client("eks", region_name=region)
    start_time = time.time()

    while True:
        try:
            response = client.describe_cluster(name=cluster_name)
            status = response["cluster"]["status"]
            print(f"Cluster status: {status}")
            
            if status == "ACTIVE":
                print("✅ Cluster is now ACTIVE.")
                return True
            elif status in ["DELETING", "FAILED"]:
                raise Exception(f"Cluster is in unexpected state: {status}")
        except client.exceptions.ResourceNotFoundException:
            print("Cluster not found. Retrying...")

        elapsed = time.time() - start_time
        if elapsed > timeout:
            raise TimeoutError(f"⏳ Cluster did not become ACTIVE within {timeout} seconds.")
        
        time.sleep(poll_interval)

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Wait for an EKS cluster to become ACTIVE.")
    parser.add_argument("--name", required=True, help="EKS cluster name")
    parser.add_argument("--region", required=True, help="AWS region (e.g., ca-central-1)")
    parser.add_argument("--timeout", type=int, default=900, help="Max wait time in seconds (default: 900)")
    parser.add_argument("--poll-interval", type=int, default=15, help="Seconds between status checks (default: 15)")
    
    args = parser.parse_args()

    try:
        wait_for_eks_cluster(args.name, args.region, args.timeout, args.poll_interval)
    except Exception as e:
        print(f"❌ Error: {e}")
        sys.exit(1)