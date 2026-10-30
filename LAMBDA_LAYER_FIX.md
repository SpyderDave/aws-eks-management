# Lambda Layer GLIBC Compatibility Fix

## Problem
The Lambda function was encountering the following error:
```
[ERROR] Runtime.ImportModuleError: Unable to import module 'index': /lib64/libc.so.6: version `GLIBC_2.28' not found (required by /opt/python/cryptography/hazmat/bindings/_rust.abi3.so)
```

## Root Cause
The `cryptography` library (a dependency of PyJWT) contains compiled binary components that were built on a system with a newer GLIBC version than what's available in the AWS Lambda runtime environment (Amazon Linux 2). When you install packages using `pip install` on your local machine (especially Windows, macOS, or newer Linux distributions), the compiled binaries may not be compatible with Lambda's runtime.

## Solution
Build the Lambda layer using Docker with the official AWS Lambda Python base image. This ensures that all dependencies, including compiled binaries like those in the `cryptography` package, are built specifically for the Lambda runtime environment.

## Steps to Fix

### 1. Rebuild the Lambda Layer
Run the appropriate build script for your operating system:

**On Linux/macOS:**
```bash
cd scripts
./build_lambda_layer.sh
```

**On Windows (PowerShell):**
```powershell
cd scripts
.\build_lambda_layer.ps1
```

**Prerequisites:**
- Docker must be installed and running
- The scripts will use the official AWS Lambda Python 3.11 image: `public.ecr.aws/lambda/python:3.11`

### 2. Upload the New Layer to S3
After the layer is built, upload it to S3:

```bash
# Set your AWS account ID and region
export ACCOUNT_ID=$(aws sts get-caller-identity --query Account --output text)
export REGION=$(aws configure get region)

# Upload the layer
aws s3 cp pyjwt-layer.zip s3://eks-helm-artifacts-${ACCOUNT_ID}-${REGION}/lambda-layers/
```

### 3. Update the Lambda Function
The CloudFormation stack will automatically pick up the new layer version when you:
- Redeploy the stack, OR
- Update the Lambda layer version manually in the AWS Console

Alternatively, you can force a Lambda layer update by incrementing the layer version in CloudFormation or updating the S3 object.

## What Changed
The build scripts (`build_lambda_layer.sh` and `build_lambda_layer.ps1`) now use Docker to build the layer in an environment that matches the Lambda runtime, AND pin the cryptography library to a version compatible with GLIBC 2.26:

**Before:**
```bash
pip install PyJWT cryptography -t $PYTHON_DIR
```

**After:**
```bash
docker run --rm \
  -v "$(pwd)/$PYTHON_DIR:/var/task" \
  public.ecr.aws/lambda/python:3.11 \
  pip install --no-cache-dir PyJWT==2.8.0 cryptography==38.0.4 -t /var/task
```

**Key changes:**
1. Uses Docker with the official Lambda Python 3.11 image for binary compatibility
2. Pins `PyJWT==2.8.0` and `cryptography==38.0.4` to specific versions known to work with GLIBC 2.26
3. Uses `--no-cache-dir` to ensure a fresh install without cached packages
4. Cryptography 38.0.4 is the last stable version before v39+ which requires GLIBC 2.28+
5. Amazon Linux 2 (Lambda runtime) only has GLIBC 2.26

## Verification
After deploying the updated layer, test the Lambda function to ensure it runs without the GLIBC error. The function should successfully:
1. Import the `jwt` module
2. Generate GitHub JWT tokens
3. Authenticate with GitHub API
4. Dispatch repository events

## Additional Notes
- Always use Docker-based builds for Lambda layers that include packages with compiled dependencies (C extensions, Rust bindings, etc.)
- Common packages that require this approach: `cryptography`, `numpy`, `pandas`, `pillow`, `psycopg2`, etc.
- The Lambda runtime uses Amazon Linux 2, which has GLIBC 2.26
