# InstaBot CI/CD Pipeline Setup Guide

This guide will help you set up a complete CI/CD pipeline for the InstaBot application using AWS CodePipeline, CodeBuild, and CloudFormation.

## Prerequisites

Before setting up the CI/CD pipeline, ensure you have:

1. **AWS CLI** installed and configured with appropriate credentials
2. **GitHub Repository** with your InstaBot code
3. **GitHub Personal Access Token** with the following permissions:
   - `repo` (full control of private repositories)
   - `admin:repo_hook` (write access to hooks)
4. **Existing AWS CloudFormation Stacks**:
   - Deployment S3 Bucket Stack (default: `InstaBot-Deployment-Bucket`)
   - Secrets Stack (default: `InstaBot-Secrets`)

## Architecture Overview

The CI/CD pipeline consists of:

```
┌─────────────┐      ┌──────────────┐      ┌───────────────┐
│   GitHub    │ ──→  │  CodeBuild   │ ──→  │ CloudFormation│
│  (Source)   │      │   (Build)    │      │    (Deploy)   │
└─────────────┘      └──────────────┘      └───────────────┘
       │                    │                       │
       └────────────────────┴───────────────────────┘
                           │
                    ┌──────▼──────┐
                    │ CodePipeline│
                    └─────────────┘
```

### Pipeline Stages

1. **Source Stage**: 
   - Pulls code from GitHub when changes are pushed
   - Uses webhook for automatic triggers

2. **Build Stage**:
   - Packages Lambda functions into ZIP files
   - Creates Lambda layers with dependencies
   - Uploads all artifacts to S3

3. **Deploy Stage**:
   - Creates CloudFormation change set
   - Executes change set to update Lambda functions and infrastructure

## Setup Instructions

### Option 1: Using PowerShell Script (Recommended for Windows)

1. Open PowerShell in the InstaBot directory

2. Run the deployment script:
   ```powershell
   .\deploy-cicd-pipeline.ps1
   ```

3. Enter the requested information:
   - GitHub Owner (your username or organization)
   - GitHub Repository name
   - GitHub Branch (default: main)
   - GitHub Personal Access Token
   - Stack names (use defaults or customize)
   - Notification email

### Option 2: Using Bash Script (Linux/Mac)

1. Make the script executable:
   ```bash
   chmod +x deploy-cicd-pipeline.sh
   ```

2. Run the deployment script:
   ```bash
   ./deploy-cicd-pipeline.sh
   ```

3. Follow the prompts to enter configuration details

### Option 3: Manual Deployment via AWS CLI

```bash
aws cloudformation create-stack \
  --stack-name InstaBot-CICD-Pipeline \
  --template-body file://cft/pipeline.yaml \
  --parameters \
    ParameterKey=GitHubOwner,ParameterValue=YOUR_GITHUB_USERNAME \
    ParameterKey=GitHubRepo,ParameterValue=InstaBot \
    ParameterKey=GitHubBranch,ParameterValue=main \
    ParameterKey=GitHubToken,ParameterValue=YOUR_GITHUB_TOKEN \
    ParameterKey=S3BucketStackName,ParameterValue=InstaBot-Deployment-Bucket \
    ParameterKey=SecretsStackName,ParameterValue=InstaBot-Secrets \
    ParameterKey=ApplicationStackName,ParameterValue=InstaBot-Application \
    ParameterKey=NotificationEmail,ParameterValue=your-email@example.com \
  --capabilities CAPABILITY_NAMED_IAM \
  --region us-west-2
```

### Option 4: Using AWS Console

1. Navigate to **CloudFormation** in AWS Console
2. Click **Create Stack** → **With new resources**
3. Upload the template: `cft/pipeline.yaml`
4. Fill in the parameters:
   - GitHubOwner: Your GitHub username
   - GitHubRepo: Repository name
   - GitHubBranch: Branch to track (e.g., main)
   - GitHubToken: Your personal access token
   - Other parameters with appropriate values
5. Check the box: "I acknowledge that AWS CloudFormation might create IAM resources"
6. Click **Create Stack**

## Post-Deployment Steps

### 1. Confirm SNS Subscription

After deployment, you'll receive an email to confirm the SNS subscription:
- Check your email inbox
- Click the confirmation link
- You'll now receive notifications about pipeline status

### 2. Verify Pipeline Creation

1. Go to **AWS CodePipeline** in the AWS Console
2. Find your pipeline: `InstaBot-CICD-Pipeline-Pipeline`
3. Verify all stages are visible: Source, Build, Deploy

### 3. Test the Pipeline

Trigger the pipeline by pushing code to your GitHub repository:

```bash
# Make a small change
echo "# CI/CD Pipeline Active" >> README.md

# Commit and push
git add README.md
git commit -m "Test CI/CD pipeline"
git push origin main
```

### 4. Monitor the Pipeline

1. **CodePipeline Console**: Watch the pipeline progress through stages
2. **CodeBuild Console**: View build logs and details
3. **CloudWatch Logs**: Check `/aws/codebuild/InstaBot-CICD-Pipeline` for detailed logs
4. **Email Notifications**: Receive success/failure notifications

## Build Process Details

The `buildspec.yml` file defines the build process:

### Build Steps

1. **Install Phase**:
   - Set up Python 3.12 runtime
   - Install AWS CLI

2. **Pre-Build Phase**:
   - Clean up old artifacts
   - Create build directories

3. **Build Phase**:
   - Package Lambda functions (main, sqs_lambda, search_engine, email_notifier)
   - Create Lambda layers with dependencies
   - Generate ZIP files for all components

4. **Post-Build Phase**:
   - Upload all artifacts to S3 bucket
   - Make CloudFormation templates available

### Build Artifacts

Generated artifacts:
- `instabot_main.zip`
- `instabot_sqs_lambda.zip`
- `instabot_search_engine.zip`
- `instabot_email_notifier.zip`
- `main_layer.zip`
- `sqs_layer.zip`
- `search_engine_py_layer.zip`
- `email_notifier_layer.zip`

## Customization

### Modify Build Settings

Edit `cft/CICD-Pipeline.yaml` and update:

```yaml
BuildComputeType: BUILD_GENERAL1_MEDIUM  # Change compute size
```

### Add Build Environment Variables

In `cft/CICD-Pipeline.yaml`, add to CodeBuild environment:

```yaml
EnvironmentVariables:
  - Name: MY_CUSTOM_VAR
    Value: my-value
```

### Change Build Timeout

In `cft/CICD-Pipeline.yaml`:

```yaml
TimeoutInMinutes: 60  # Increase to 60 minutes
```

### Add Manual Approval Stage

Add between Build and Deploy stages in `cft/CICD-Pipeline.yaml`:

```yaml
- Name: ManualApproval
  Actions:
    - Name: ApproveDeployment
      ActionTypeId:
        Category: Approval
        Owner: AWS
        Provider: Manual
        Version: '1'
      Configuration:
        NotificationArn: !Ref PipelineNotificationTopic
        CustomData: "Please review and approve deployment"
```

## Troubleshooting

### Pipeline Fails at Build Stage

**Issue**: Build fails with dependency errors

**Solution**:
1. Check CodeBuild logs in CloudWatch
2. Verify `requirements.txt` files are correct
3. Ensure all dependencies are compatible with Lambda runtime

### Pipeline Fails at Deploy Stage

**Issue**: CloudFormation deployment fails

**Solution**:
1. Check CloudFormation events in AWS Console
2. Verify IAM permissions for CloudFormation role
3. Ensure parameter values are correct

### GitHub Webhook Not Triggering

**Issue**: Pipeline doesn't start when code is pushed

**Solution**:
1. Check GitHub repository settings → Webhooks
2. Verify webhook URL is correct
3. Regenerate webhook in AWS Console if needed

### S3 Access Denied Errors

**Issue**: Build stage can't upload to S3

**Solution**:
1. Verify S3 bucket exists and is accessible
2. Check CodeBuild IAM role permissions
3. Ensure bucket policy allows CodeBuild access

## Monitoring and Logs

### CodePipeline Logs
- **Location**: CodePipeline Console → Pipeline → Execution History
- **Shows**: Stage transitions, success/failure status

### CodeBuild Logs
- **Location**: CloudWatch Logs → `/aws/codebuild/InstaBot-CICD-Pipeline`
- **Shows**: Detailed build output, command execution

### CloudFormation Logs
- **Location**: CloudFormation Console → Stack → Events tab
- **Shows**: Resource creation/update status, errors

## Cleanup

To delete the CI/CD pipeline:

```bash
aws cloudformation delete-stack \
  --stack-name InstaBot-CICD-Pipeline \
  --region us-west-2
```

**Note**: This will delete:
- CodePipeline
- CodeBuild project
- Pipeline artifact S3 bucket (including contents)
- IAM roles and policies
- SNS topic
- EventBridge rules

The application stack will remain deployed.

## Best Practices

1. **Use Separate Branches**: 
   - `dev` branch → Development environment
   - `staging` branch → Staging environment
   - `main` branch → Production environment

2. **Add Tests**: 
   - Include unit tests in build stage
   - Add integration tests before deploy

3. **Manual Approvals**: 
   - Add approval stage for production deployments
   - Review changes before executing

4. **Monitor Costs**:
   - Set up billing alerts
   - Use S3 lifecycle policies for old artifacts
   - Consider smaller CodeBuild instance types

5. **Security**:
   - Never commit GitHub tokens to repository
   - Use AWS Secrets Manager for sensitive values
   - Rotate GitHub tokens regularly

## Additional Resources

- [AWS CodePipeline Documentation](https://docs.aws.amazon.com/codepipeline/)
- [AWS CodeBuild Documentation](https://docs.aws.amazon.com/codebuild/)
- [CloudFormation Best Practices](https://docs.aws.amazon.com/AWSCloudFormation/latest/UserGuide/best-practices.html)
- [GitHub Personal Access Tokens](https://docs.github.com/en/authentication/keeping-your-account-and-data-secure/creating-a-personal-access-token)

## Support

For issues or questions:
1. Check CloudWatch logs for detailed error messages
2. Review AWS service quotas and limits
3. Verify all prerequisites are met
4. Check IAM permissions for all roles

---

**Congratulations!** 🎉 Your InstaBot CI/CD pipeline is now set up. Every push to your GitHub repository will automatically build and deploy your application to AWS.

