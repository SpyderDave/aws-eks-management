#!/usr/bin/env python3

import boto3
import sys
import argparse

def parse_args():
    parser = argparse.ArgumentParser(description='Check EKS cluster tags')
    parser.add_argument('--cluster-name', required=True, help='Name of the EKS cluster')
    parser.add_argument('--region', required=True, help='AWS region of the cluster')
    return parser.parse_args()

def get_cluster_tags(cluster_name, region):
    try:
        eks_client = boto3.client('eks', region_name=region)
        response = eks_client.describe_cluster(name=cluster_name)
        return response['cluster'].get('tags', {})
    except Exception as e:
        print(f"Error getting cluster tags: {e}")
        sys.exit(1)

def check_tags(tags):
    # Check "Managed" tag
    managed = tags.get('Managed', '').lower()
    if managed not in ['true']:
        print("Error: 'Managed' tag is not present or not set to 'True'")
        return False

    # Check "environment" tag
    environment = tags.get('environment', '').lower()
    valid_environments = ['nonp', 'prod']
    if environment not in valid_environments:
        print("Error: 'environment' tag is not set to 'nonp' or 'prod'")
        return False

    return True

def main():
    args = parse_args()
    tags = get_cluster_tags(args.cluster_name, args.region)
    
    if check_tags(tags):
        sys.exit(0)
    else:
        sys.exit(1)

if __name__ == "__main__":
    main()
