#!/bin/bash

# Deploy InstaBot CI/CD Pipeline
# This script deploys the complete CI/CD infrastructure for InstaBot

set -e

echo "=================================================="
echo "InstaBot CI/CD Pipeline Deployment Script"
echo "=================================================="

# Configuration
STACK_NAME="InstaBot-CICD-Pipeline"
TEMPLATE_FILE="cft/pipeline.yaml"
REGION="us-west-2"

# Prompt for parameters
read -p "Enter GitHub Owner (username/organization): " GITHUB_OWNER
read -p "Enter GitHub Repository Name [InstaBot]: " GITHUB_REPO
GITHUB_REPO=${GITHUB_REPO:-InstaBot}
read -p "Enter GitHub Branch [main]: " GITHUB_BRANCH
GITHUB_BRANCH=${GITHUB_BRANCH:-main}
read -sp "Enter GitHub Personal Access Token: " GITHUB_TOKEN
echo ""
read -p "Enter S3 Bucket Stack Name [InstaBot-Deployment-Bucket]: " S3_STACK
S3_STACK=${S3_STACK:-InstaBot-Deployment-Bucket}
read -p "Enter Secrets Stack Name [InstaBot-Secrets]: " SECRETS_STACK
SECRETS_STACK=${SECRETS_STACK:-InstaBot-Secrets}
read -p "Enter Application Stack Name [InstaBot-Application]: " APP_STACK
APP_STACK=${APP_STACK:-InstaBot-Application}
read -p "Enter Notification Email: " NOTIFICATION_EMAIL

echo ""
echo "Deploying CI/CD Pipeline Stack..."
echo "Stack Name: $STACK_NAME"
echo "Region: $REGION"
echo "GitHub: $GITHUB_OWNER/$GITHUB_REPO (branch: $GITHUB_BRANCH)"
echo ""

# Deploy the CloudFormation stack
aws cloudformation create-stack \
  --stack-name "$STACK_NAME" \
  --template-body file://"$TEMPLATE_FILE" \
  --parameters \
    ParameterKey=GitHubOwner,ParameterValue="$GITHUB_OWNER" \
    ParameterKey=GitHubRepo,ParameterValue="$GITHUB_REPO" \
    ParameterKey=GitHubBranch,ParameterValue="$GITHUB_BRANCH" \
    ParameterKey=GitHubToken,ParameterValue="$GITHUB_TOKEN" \
    ParameterKey=S3BucketStackName,ParameterValue="$S3_STACK" \
    ParameterKey=SecretsStackName,ParameterValue="$SECRETS_STACK" \
    ParameterKey=ApplicationStackName,ParameterValue="$APP_STACK" \
    ParameterKey=NotificationEmail,ParameterValue="$NOTIFICATION_EMAIL" \
  --capabilities CAPABILITY_NAMED_IAM \
  --region "$REGION"

echo ""
echo "Waiting for stack creation to complete..."
aws cloudformation wait stack-create-complete \
  --stack-name "$STACK_NAME" \
  --region "$REGION"

echo ""
echo "=================================================="
echo "CI/CD Pipeline Deployed Successfully!"
echo "=================================================="

# Get outputs
PIPELINE_URL=$(aws cloudformation describe-stacks \
  --stack-name "$STACK_NAME" \
  --query 'Stacks[0].Outputs[?OutputKey==`PipelineUrl`].OutputValue' \
  --output text \
  --region "$REGION")

echo ""
echo "Pipeline URL: $PIPELINE_URL"
echo ""
echo "Next Steps:"
echo "1. Check your email ($NOTIFICATION_EMAIL) to confirm SNS subscription"
echo "2. Push code to your GitHub repository to trigger the pipeline"
echo "3. Monitor the pipeline at: $PIPELINE_URL"
echo ""

