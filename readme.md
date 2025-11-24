# 🎵 InstaBot - Instagram Music Recognition System

A serverless AWS-based application that automatically processes Instagram direct messages containing video clips, identifies songs using audio recognition, and sends the results back to users via email and Instagram messages.

## 🏗️ Architecture Overview

```
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│   Instagram     │    │   SQS Lambda    │    │  Search Engine  │    │ Email Notifier  │
│   Messages      │───▶│   (Trigger)     │───▶│    Lambda       │───▶│    Lambda       │
│                 │    │                 │    │                 │    │                 │
└─────────────────┘    └─────────────────┘    └─────────────────┘    └─────────────────┘
         │                       │                       │                       │
         │                       ▼                       ▼                       ▼
         │              ┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
         │              │   SQS Queue     │    │   Audio API     │    │   Gmail SMTP    │
         │              │                 │    │  (RapidAPI)     │    │                 │
         │              └─────────────────┘    └─────────────────┘    └─────────────────┘
         │
         ▼
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│   S3 Bucket     │    │   DynamoDB      │    │   CloudWatch    │
│ (Session Store) │    │   (Sessions)    │    │    (Logs)       │
└─────────────────┘    └─────────────────┘    └─────────────────┘
```

## 🚀 Quick Start

### Prerequisites
- AWS CLI configured with appropriate permissions
- Docker installed (for Lambda layer creation)
- Python 3.9+ for local development
- GitHub account with repository
- GitHub Personal Access Token (for CI/CD)

## 🔄 CI/CD Pipeline (Automated Deployment)

This project includes a complete CI/CD pipeline using AWS CodePipeline. **This is the recommended deployment method.**

### Quick CI/CD Setup

1. **Review the Quick Start Guide**:
   ```bash
   # See QUICK-START.md for a 3-step setup process
   ```

2. **Deploy the CI/CD Pipeline**:
   
   **PowerShell (Windows):**
   ```powershell
   .\deploy-cicd-pipeline.ps1
   ```
   
   **Bash (Linux/Mac):**
   ```bash
   chmod +x deploy-cicd-pipeline.sh
   ./deploy-cicd-pipeline.sh
   ```

3. **Push Code to Trigger Automatic Deployment**:
   ```bash
   git add .
   git commit -m "Deploy via CI/CD"
   git push origin main
   ```

### What the CI/CD Pipeline Does

- ✅ **Automatically builds** Lambda functions and layers on every push
- ✅ **Packages dependencies** with correct architecture for Lambda
- ✅ **Uploads artifacts** to S3
- ✅ **Deploys infrastructure** via CloudFormation
- ✅ **Sends notifications** on success/failure
- ✅ **Zero manual steps** after initial setup

### CI/CD Documentation

- 📘 **Detailed Setup**: See [`CICD-SETUP.md`](CICD-SETUP.md) for complete documentation
- 🏗️ **Build Configuration**: See [`buildspec.yml`](buildspec.yml) for build process
- ☁️ **Pipeline Infrastructure**: See [`cft/pipeline.yaml`](cft/pipeline.yaml) for pipeline template

---

## 📦 Manual Deployment (Alternative)

If you prefer manual deployment instead of CI/CD:

### 1. Deploy Infrastructure

```bash
# Deploy S3 bucket for deployment artifacts
aws cloudformation deploy \
  --template-file cft/Deployment-bucket.yaml \
  --stack-name instabot-deployment-bucket

# Deploy secrets (update with your credentials first)
aws cloudformation deploy \
  --template-file cft/secrets.yaml \
  --stack-name instabot-secrets \
  --capabilities CAPABILITY_IAM

# Deploy main application stack
aws cloudformation deploy \
  --template-file cft/Application-stack.yaml \
  --stack-name instabot-app \
  --parameter-overrides \
    SecretsStackName=instabot-secrets \
    S3BucketStackName=instabot-deployment-bucket \
  --capabilities CAPABILITY_IAM
```

### 2. Package and Deploy Lambda Functions Manually

**Option A: Use the manual build script**:

**PowerShell:**
```powershell
.\scripts\manual-build.ps1 -S3Bucket your-bucket-name
```

**Bash:**
```bash
chmod +x scripts/manual-build.sh
./scripts/manual-build.sh your-bucket-name
```

**Option B: Follow manual packaging instructions below**, then upload the ZIP files to your S3 deployment bucket and update the Lambda functions.

## 📦 Lambda Function Packaging

### Lambda Layer Creation

Create a Lambda layer with shared dependencies using Docker:

```bash
# Create layer for instabot_sqs_lambda dependencies
docker run --rm --entrypoint "" \
  -v "${PWD}/instabot_sqs_lambda:/var/task" \
  public.ecr.aws/lambda/python:3.12 \
  sh -c "cd /var/task && pip install -r requirements.txt -t ./python"

# Zip the layer
cd instabot_sqs_lambda && zip -r ../instabot_layer.zip python && cd ..
```

### Lambda Function Packaging

Package each Lambda function:

```bash
# Package SQS Lambda
cd instabot_sqs_lambda/
zip -r ../instabot_sqs_lambda.zip . --exclude="python/*"
cd ..

# Package Search Engine Lambda  
cd instabot_search_engine/
zip -r ../instabot_search_engine.zip .
cd ..

# Package Email Notifier Lambda
cd instabot_email_notifier/
zip -r ../instabot_email_notifier.zip .
cd ..
```

## 🔧 Lambda Functions Explained

### 1. 📨 SQS Lambda (`instabot_sqs_lambda`)

**Purpose**: Entry point that monitors Instagram DMs and queues processing tasks

**Functionality**:
- 🔐 Authenticates with Instagram using stored S3 session
- 📬 Checks for unread direct messages containing video clips
- 🎬 Extracts video URLs from Instagram clips/reels
- 📤 Sends extracted data to SQS queue for processing
- 🗑️ Hides processed message threads

**Key Features**:
- Session persistence via S3 for reliable Instagram authentication
- Automatic fallback to credential-based login if session expires
- Robust error handling and logging

**Environment Variables**:
```bash
username=your_instagram_username
password=your_instagram_password
SQS_QUEUE_URL=your_sqs_queue_url
Bucket_name=your_s3_bucket_name
```

**Dependencies**: `instagrapi`, `pillow`, `pandas`, `psycopg2-binary`

---

### 2. 🔍 Search Engine Lambda (`instabot_search_engine`)

**Purpose**: Processes audio from videos and identifies songs using AI recognition

**Functionality**:
- 🎵 Downloads audio from Instagram video URLs
- ✂️ Extracts and processes audio segments using FFmpeg
- 🤖 Sends audio to RapidAPI's Shazam-like service for song identification
- 🔄 Tries multiple time segments if initial recognition fails
- 🔗 Generates YouTube and YouTube Music links for identified songs
- 📧 Triggers email notification with results

**Key Features**:
- Multi-attempt recognition strategy (tries 3 different time segments)
- Automatic temporary file cleanup
- Base64 audio encoding for API compatibility
- Batch processing support via SQS

**Environment Variables**:
```bash
api_host=your_rapidapi_host
api_key=your_rapidapi_key
content_type=text/plain
email_lambda_name=your_email_lambda_arn
```

**Dependencies**: `requests`
**Lambda Layer Requirements**: FFmpeg binary for audio processing

---

### 3. ✉️ Email Notifier Lambda (`instabot_email_notifier`)

**Purpose**: Sends formatted email notifications and Instagram responses with song results

**Functionality**:
- 📧 Composes HTML email with song identification results
- 📊 Creates formatted table with song names and streaming links
- 📮 Sends email via Gmail SMTP
- 💬 Sends song links back to original Instagram thread
- 🗑️ Cleans up Instagram conversation after sending results

**Key Features**:
- Professional HTML email formatting
- Dual delivery: email + Instagram DM
- Instagram session management with S3 persistence
- Comprehensive error handling and logging

**Environment Variables**:
```bash
sender_email=your_gmail_address
sender_password=your_gmail_app_password
receiver_email=recipient_email_address
instagram_username=your_instagram_username
instagram_password=your_instagram_password
bucket_name=your_s3_bucket_name
```

**Dependencies**: `instagrapi`, `pillow`, `pandas`, `psycopg2-binary`

## 🔐 Configuration

### Required Secrets (stored in AWS Secrets Manager)

```json
{
  "instagram_username": "your_instagram_username",
  "instagram_password": "your_instagram_password", 
  "gmail_username": "your_gmail_address",
  "gmail_password": "your_gmail_app_password",
  "rapidapi_key": "your_rapidapi_key",
  "rapidapi_host": "shazam-api-host"
}
```

### Environment Variables Setup

Update the CloudFormation template or Lambda console with:
- Instagram credentials for DM access
- Gmail credentials for email notifications  
- RapidAPI credentials for song recognition
- S3 bucket names for session storage
- SQS queue URLs for message passing

## 🛠️ Development

### Local Testing

```bash
# Install dependencies
pip install -r requirements.txt

# Set environment variables
export instagram_username="your_username"
export instagram_password="your_password"
# ... other variables

# Test individual functions
python -c "from instabot_sqs_lambda.lambda_function import lambda_handler; lambda_handler({}, {})"
```

### Monitoring

- 📊 CloudWatch Logs: Monitor function execution and errors
- 📈 CloudWatch Metrics: Track invocation counts and duration
- 🚨 SQS DLQ: Failed messages are sent to Dead Letter Queue
- 📧 Email notifications provide user-facing status updates

## 🏗️ Infrastructure Components

### AWS Services Used
- **Lambda**: Serverless function execution
- **SQS**: Message queuing between functions
- **S3**: Session storage and deployment artifacts
- **DynamoDB**: Session metadata storage
- **CloudWatch**: Logging and monitoring
- **Secrets Manager**: Secure credential storage
- **IAM**: Permission management

### External Services
- **Instagram Graph API**: Direct message access
- **RapidAPI (Shazam)**: Audio recognition service
- **Gmail SMTP**: Email delivery
- **YouTube**: Music link generation

## 🔄 Workflow

1. **Message Detection**: SQS Lambda monitors Instagram DMs
2. **Content Extraction**: Extracts video URLs from messages
3. **Queue Processing**: Sends data to SQS for async processing
4. **Audio Analysis**: Search Engine Lambda downloads and processes audio
5. **Song Recognition**: Identifies songs using external API
6. **Result Delivery**: Email Notifier sends results via email and Instagram
7. **Cleanup**: Removes processed messages and temporary files

## 🚨 Troubleshooting

### Common Issues

**Instagram Authentication Fails**:
- Check credentials in Secrets Manager
- Verify S3 session file exists and is valid
- Instagram may require 2FA - use app-specific password

**Song Recognition Not Working**:
- Verify RapidAPI key and host are correct
- Check FFmpeg layer is attached to Search Engine Lambda
- Audio quality may be too poor for recognition

**Email Delivery Issues**:
- Enable Gmail "Less secure app access" or use App Password
- Check sender/receiver email addresses
- Verify SMTP settings (Gmail: smtp.gmail.com:587)

### Monitoring Commands

```bash
# Check Lambda logs
aws logs describe-log-groups --log-group-name-prefix "/aws/lambda/instabot"

# Monitor SQS queue
aws sqs get-queue-attributes --queue-url YOUR_QUEUE_URL --attribute-names All

# Check S3 session file
aws s3 ls s3://your-bucket-name/instagram_session.json
```

## 📄 License

This project is licensed under the MIT License - see the LICENSE file for details.

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add tests if applicable
5. Submit a pull request

## 📞 Support

For issues and questions:
- Check the troubleshooting section above
- Review CloudWatch logs for detailed error messages
- Ensure all environment variables are properly configured
- Verify AWS permissions are correctly set

---

**⚠️ Important Notes**:
- This application processes Instagram content - ensure compliance with Instagram's Terms of Service
- Audio recognition API has usage limits - monitor your RapidAPI quotas
- Keep your credentials secure and rotate them regularly
- Test thoroughly in a development environment before production deployment