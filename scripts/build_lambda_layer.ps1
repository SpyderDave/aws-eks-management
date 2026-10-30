# PowerShell script to build Lambda Layer for PyJWT dependency

Write-Host "Building Lambda Layer for PyJWT..." -ForegroundColor Green

# Create temporary directory structure
$LAYER_DIR = "lambda-layer-build"
$PYTHON_DIR = "$LAYER_DIR\python"

# Clean up any existing build directory
if (Test-Path $LAYER_DIR) {
    Remove-Item -Recurse -Force $LAYER_DIR
}
New-Item -ItemType Directory -Path $PYTHON_DIR -Force | Out-Null

# Install PyJWT and its dependencies into the python directory
# Use Docker to build for Lambda's Amazon Linux 2 environment to ensure GLIBC compatibility
# Pin cryptography to 38.0.4 - last version before Rust bindings required GLIBC 2.28
Write-Host "Installing PyJWT and cryptography using Docker for Lambda compatibility..." -ForegroundColor Yellow
docker run --rm `
  -v "${PWD}\${PYTHON_DIR}:/var/task" `
  public.ecr.aws/lambda/python:3.11 `
  pip install --no-cache-dir PyJWT==2.8.0 cryptography==38.0.4 -t /var/task

# Create the zip file
Write-Host "Creating layer zip file..." -ForegroundColor Yellow
Compress-Archive -Path "$LAYER_DIR\python" -DestinationPath "pyjwt-layer.zip" -Force

# Clean up
Remove-Item -Recurse -Force $LAYER_DIR

Write-Host "`nLambda Layer package created: pyjwt-layer.zip" -ForegroundColor Green
Write-Host "`nNext steps:" -ForegroundColor Cyan
Write-Host "1. Upload pyjwt-layer.zip to S3:"
Write-Host "   aws s3 cp pyjwt-layer.zip s3://eks-helm-artifacts-`${ACCOUNT_ID}-`${REGION}/lambda-layers/" -ForegroundColor White
Write-Host "`n2. Deploy the CloudFormation stack with the updated template" -ForegroundColor White
