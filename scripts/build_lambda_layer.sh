#!/bin/bash
# Script to build Lambda Layer for PyJWT dependency

set -e

echo "Building Lambda Layer for PyJWT..."

# Create temporary directory structure
LAYER_DIR="lambda-layer-build"
PYTHON_DIR="$LAYER_DIR/python"

# Clean up any existing build directory
rm -rf $LAYER_DIR
mkdir -p $PYTHON_DIR

# Install PyJWT and its dependencies into the python directory
# Use Docker to build for Lambda's Amazon Linux 2 environment to ensure GLIBC compatibility
# Pin cryptography to 38.0.4 - last version before Rust bindings required GLIBC 2.28
echo "Installing PyJWT and cryptography using Docker for Lambda compatibility..."
docker run --rm \
  -v "$(pwd)/$PYTHON_DIR:/var/task" \
  public.ecr.aws/lambda/python:3.11 \
  pip install --no-cache-dir PyJWT==2.8.0 cryptography==38.0.4 -t /var/task

# Create the zip file
echo "Creating layer zip file..."
cd $LAYER_DIR
zip -r ../pyjwt-layer.zip python/
cd ..

# Clean up
rm -rf $LAYER_DIR

echo "Lambda Layer package created: pyjwt-layer.zip"
echo ""
echo "Next steps:"
echo "1. Upload pyjwt-layer.zip to S3:"
echo "   aws s3 cp pyjwt-layer.zip s3://eks-helm-artifacts-\${ACCOUNT_ID}-\${REGION}/lambda-layers/"
echo ""
echo "2. Deploy the CloudFormation stack with the updated template"
