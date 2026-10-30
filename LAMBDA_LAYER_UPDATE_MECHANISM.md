# Lambda Layer Auto-Update Mechanism

## Problem Statement

When a Lambda Layer's S3 object is updated, CloudFormation doesn't automatically detect the change because it only tracks the S3 bucket and key, not the object's content or version. This means:

1. Uploading a new `pyjwt-layer.zip` to S3 doesn't trigger a new Lambda Layer version
2. The Lambda function continues using the old layer version
3. Bug fixes (like the GLIBC compatibility fix) don't get applied automatically

## Solution Overview

We've implemented a mechanism that forces CloudFormation to create a new Lambda Layer version whenever the S3 object changes by:

1. **Adding a version parameter** to the CloudFormation template
2. **Tracking the S3 object version** (or timestamp if versioning is disabled)
3. **Passing the version** through the deployment pipeline
4. **Using the version in the layer description** to trigger CloudFormation updates

## How It Works

### 1. CloudFormation Template Changes

**File:** `templates/helm-deploy-charts.yaml`

Added a new parameter:
```yaml
Parameters:
  LayerS3ObjectVersion:
    Type: String
    Description: S3 Object Version of the Lambda Layer zip file (forces layer update)
    Default: "latest"
```

Updated the Lambda Layer resource to use this parameter:
```yaml
PyJWTLayer:
  Type: AWS::Lambda::LayerVersion
  Properties:
    LayerName: pyjwt-layer
    Description: !Sub "PyJWT and cryptography libraries - Version: ${LayerS3ObjectVersion}"
    Content:
      S3Bucket: !Sub "eks-helm-artifacts-${AWS::AccountId}-${AWS::Region}"
      S3Key: lambda-layers/pyjwt-layer.zip
    CompatibleRuntimes:
      - python3.11
      - python3.12
  DeletionPolicy: Retain
```

**Key Point:** When `LayerS3ObjectVersion` changes, the `Description` changes, which forces CloudFormation to create a new `LayerVersion` resource. The Lambda function automatically uses the new layer version because it references `!Ref PyJWTLayer`.

### 2. Configuration File Changes

**File:** `config/platform/helm-deploy-charts.yaml`

Added the parameter mapping:
```yaml
parameters:
  LayerS3ObjectVersion: "{{ environment_variable.LayerS3ObjectVersion | default('latest') }}"
```

This tells the Stack Deployer deployment system to pass the `LayerS3ObjectVersion` environment variable as a CloudFormation parameter.

### 3. GitHub Actions Workflow Changes

**File:** `.github/workflows/deployment.yml`

Added a step to retrieve the S3 object version before deployment:
```yaml
- name: Get S3 Object Version
  id: get_s3_version
  run: |
    BUCKET_NAME="${{ needs.DeployS3Bucket.outputs.bucket_name }}"
    S3_VERSION=$(aws s3api head-object \
      --bucket "$BUCKET_NAME" \
      --key lambda-layers/pyjwt-layer.zip \
      --query 'VersionId' \
      --output text 2>/dev/null || echo "$(date +%s)")
    
    echo "s3_version=$S3_VERSION" >> $GITHUB_OUTPUT
    echo "Lambda Layer S3 Version: $S3_VERSION"
```

Then pass it as an environment variable to the deployment:
```yaml
env:
  LayerS3ObjectVersion: ${{ steps.get_s3_version.outputs.s3_version }}
```

## Deployment Flow

1. **Build Lambda Layer** - GitHub Actions builds the layer with correct dependencies
2. **Upload to S3** - The layer zip is uploaded to S3
3. **Get S3 Version** - Retrieve the S3 object version ID (or use timestamp)
4. **Deploy CloudFormation** - Pass the version as a parameter
5. **CloudFormation Detects Change** - The changed `Description` triggers a new layer version
6. **Lambda Updates** - The Lambda function automatically uses the new layer version

## Benefits

✅ **Automatic Updates** - Lambda functions always use the latest layer version after deployment  
✅ **No Manual Intervention** - The entire process is automated  
✅ **Version Tracking** - The layer description shows which S3 version it was built from  
✅ **Rollback Safety** - Old layer versions are retained (DeletionPolicy: Retain)  
✅ **Works Without S3 Versioning** - Falls back to timestamp if versioning is disabled  

## Verification

After deployment, you can verify the layer is updated:

```bash
# Check the Lambda function's layer version
aws lambda get-function --function-name eks-github-dispatch \
  --query 'Configuration.Layers[0].Arn' --output text

# Check the layer description
aws lambda get-layer-version \
  --layer-name pyjwt-layer \
  --version-number <VERSION> \
  --query 'Description' --output text
```

The description should show the S3 version ID or timestamp from the latest deployment.

## Troubleshooting

### Layer Not Updating

1. **Check the GitHub Actions logs** - Verify the S3 version was retrieved
2. **Check CloudFormation parameters** - Ensure `LayerS3ObjectVersion` is being passed
3. **Check the layer description** - It should change with each deployment

### S3 Versioning Not Enabled

If S3 versioning is not enabled on the bucket, the workflow falls back to using a timestamp:
```bash
S3_VERSION=$(aws s3api head-object ... || echo "$(date +%s)")
```

This still works because the timestamp changes with each deployment.

## Related Files

- `templates/helm-deploy-charts.yaml` - CloudFormation template
- `config/platform/helm-deploy-charts.yaml` - Stack Deployer configuration
- `.github/workflows/deployment.yml` - GitHub Actions workflow
- `scripts/build_lambda_layer.sh` - Layer build script (Linux/macOS)
- `scripts/build_lambda_layer.ps1` - Layer build script (Windows)
- `LAMBDA_LAYER_FIX.md` - GLIBC compatibility fix documentation

## Additional Notes

- The `DeletionPolicy: Retain` ensures old layer versions aren't deleted when the stack updates
- This allows rollback to previous versions if needed
- Lambda automatically limits the number of layer versions per layer (default: 75)
- Old versions can be manually cleaned up if needed
