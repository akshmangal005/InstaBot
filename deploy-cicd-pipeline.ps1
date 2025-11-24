# Deploy InstaBot CI/CD Pipeline (PowerShell version)
# This script deploys the complete CI/CD infrastructure for InstaBot

$ErrorActionPreference = "Stop"

Write-Host "==================================================" -ForegroundColor Cyan
Write-Host "InstaBot CI/CD Pipeline Deployment Script" -ForegroundColor Cyan
Write-Host "==================================================" -ForegroundColor Cyan

# Configuration
$STACK_NAME = "InstaBot-CICD-Pipeline"
$TEMPLATE_FILE = "cft/pipeline.yaml"
$REGION = "us-west-2"

# Prompt for parameters
$GITHUB_OWNER = Read-Host "Enter GitHub Owner (username/organization)"
$GITHUB_REPO = Read-Host "Enter GitHub Repository Name [InstaBot]"
if ([string]::IsNullOrWhiteSpace($GITHUB_REPO)) { $GITHUB_REPO = "InstaBot" }

$GITHUB_BRANCH = Read-Host "Enter GitHub Branch [main]"
if ([string]::IsNullOrWhiteSpace($GITHUB_BRANCH)) { $GITHUB_BRANCH = "main" }

$GITHUB_TOKEN = Read-Host "Enter GitHub Personal Access Token" -AsSecureString
$GITHUB_TOKEN_PLAIN = [Runtime.InteropServices.Marshal]::PtrToStringAuto(
    [Runtime.InteropServices.Marshal]::SecureStringToBSTR($GITHUB_TOKEN)
)

$S3_STACK = Read-Host "Enter S3 Bucket Stack Name [InstaBot-Deployment-Bucket]"
if ([string]::IsNullOrWhiteSpace($S3_STACK)) { $S3_STACK = "InstaBot-Deployment-Bucket" }

$SECRETS_STACK = Read-Host "Enter Secrets Stack Name [InstaBot-Secrets]"
if ([string]::IsNullOrWhiteSpace($SECRETS_STACK)) { $SECRETS_STACK = "InstaBot-Secrets" }

$APP_STACK = Read-Host "Enter Application Stack Name [InstaBot-Application]"
if ([string]::IsNullOrWhiteSpace($APP_STACK)) { $APP_STACK = "InstaBot-Application" }

$NOTIFICATION_EMAIL = Read-Host "Enter Notification Email"

Write-Host ""
Write-Host "Deploying CI/CD Pipeline Stack..." -ForegroundColor Yellow
Write-Host "Stack Name: $STACK_NAME"
Write-Host "Region: $REGION"
Write-Host "GitHub: $GITHUB_OWNER/$GITHUB_REPO (branch: $GITHUB_BRANCH)"
Write-Host ""

# Deploy the CloudFormation stack
aws cloudformation create-stack `
  --stack-name "$STACK_NAME" `
  --template-body "file://$TEMPLATE_FILE" `
  --parameters `
    "ParameterKey=GitHubOwner,ParameterValue=$GITHUB_OWNER" `
    "ParameterKey=GitHubRepo,ParameterValue=$GITHUB_REPO" `
    "ParameterKey=GitHubBranch,ParameterValue=$GITHUB_BRANCH" `
    "ParameterKey=GitHubToken,ParameterValue=$GITHUB_TOKEN_PLAIN" `
    "ParameterKey=S3BucketStackName,ParameterValue=$S3_STACK" `
    "ParameterKey=SecretsStackName,ParameterValue=$SECRETS_STACK" `
    "ParameterKey=ApplicationStackName,ParameterValue=$APP_STACK" `
    "ParameterKey=NotificationEmail,ParameterValue=$NOTIFICATION_EMAIL" `
  --capabilities CAPABILITY_NAMED_IAM `
  --region "$REGION"

Write-Host ""
Write-Host "Waiting for stack creation to complete..." -ForegroundColor Yellow
aws cloudformation wait stack-create-complete `
  --stack-name "$STACK_NAME" `
  --region "$REGION"

Write-Host ""
Write-Host "==================================================" -ForegroundColor Green
Write-Host "CI/CD Pipeline Deployed Successfully!" -ForegroundColor Green
Write-Host "==================================================" -ForegroundColor Green

# Get outputs
$PIPELINE_URL = aws cloudformation describe-stacks `
  --stack-name "$STACK_NAME" `
  --query 'Stacks[0].Outputs[?OutputKey==`PipelineUrl`].OutputValue' `
  --output text `
  --region "$REGION"

Write-Host ""
Write-Host "Pipeline URL: $PIPELINE_URL" -ForegroundColor Cyan
Write-Host ""
Write-Host "Next Steps:" -ForegroundColor Yellow
Write-Host "1. Check your email ($NOTIFICATION_EMAIL) to confirm SNS subscription"
Write-Host "2. Push code to your GitHub repository to trigger the pipeline"
Write-Host "3. Monitor the pipeline at: $PIPELINE_URL"
Write-Host ""

