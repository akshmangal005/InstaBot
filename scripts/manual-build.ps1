# Manual Build Script for InstaBot (PowerShell)
# This script mimics the CodeBuild process locally for testing

param(
    [Parameter(Mandatory=$true)]
    [string]$S3Bucket
)

$ErrorActionPreference = "Stop"

Write-Host "========================================" -ForegroundColor Cyan
Write-Host "InstaBot Manual Build Script" -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan

# Configuration
$BUILD_DIR = "build-output"

Write-Host "S3 Bucket: $S3Bucket"
Write-Host "Build Directory: $BUILD_DIR"
Write-Host ""

# Clean up
Write-Host "Cleaning up previous builds..." -ForegroundColor Yellow
if (Test-Path $BUILD_DIR) {
    Remove-Item -Path $BUILD_DIR -Recurse -Force
}
New-Item -ItemType Directory -Path $BUILD_DIR | Out-Null

# Package Lambda Functions
Write-Host "========================================" -ForegroundColor Cyan
Write-Host "Packaging Lambda Functions..." -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan

Write-Host "Packaging instabot_main..."
Set-Location instabot_main
Compress-Archive -Path lambda_function.py -DestinationPath "..\$BUILD_DIR\instabot_main.zip" -Force
Set-Location ..

Write-Host "Packaging instabot_sqs_lambda..."
Set-Location instabot_sqs_lambda
Compress-Archive -Path lambda_function.py -DestinationPath "..\$BUILD_DIR\instabot_sqs_lambda.zip" -Force
Set-Location ..

Write-Host "Packaging instabot_search_engine..."
Set-Location instabot_search_engine
Compress-Archive -Path lambda_function.py -DestinationPath "..\$BUILD_DIR\instabot_search_engine.zip" -Force
Set-Location ..

Write-Host "Packaging instabot_email_notifier..."
Set-Location instabot_email_notifier
Compress-Archive -Path lambda_function.py -DestinationPath "..\$BUILD_DIR\instabot_email_notifier.zip" -Force
Set-Location ..

# Build Lambda Layers
Write-Host "========================================" -ForegroundColor Cyan
Write-Host "Building Lambda Layers..." -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan

Write-Host "Building main_layer..."
New-Item -ItemType Directory -Path "$BUILD_DIR\main_layer\python" -Force | Out-Null
pip install -r instabot_main\requirements.txt -t "$BUILD_DIR\main_layer\python" --platform manylinux2014_x86_64 --only-binary=:all:
Set-Location "$BUILD_DIR\main_layer"
Compress-Archive -Path python -DestinationPath "..\main_layer.zip" -Force
Set-Location ..\..

Write-Host "Building sqs_layer..."
New-Item -ItemType Directory -Path "$BUILD_DIR\sqs_layer\python" -Force | Out-Null
pip install -r instabot_sqs_lambda\requirements.txt -t "$BUILD_DIR\sqs_layer\python" --platform manylinux2014_x86_64 --only-binary=:all:
Set-Location "$BUILD_DIR\sqs_layer"
Compress-Archive -Path python -DestinationPath "..\sqs_layer.zip" -Force
Set-Location ..\..

Write-Host "Building search_engine_py_layer..."
New-Item -ItemType Directory -Path "$BUILD_DIR\search_engine_py_layer\python" -Force | Out-Null
pip install -r instabot_search_engine\requirements.txt -t "$BUILD_DIR\search_engine_py_layer\python" --platform manylinux2014_x86_64 --only-binary=:all:
Set-Location "$BUILD_DIR\search_engine_py_layer"
Compress-Archive -Path python -DestinationPath "..\search_engine_py_layer.zip" -Force
Set-Location ..\..

Write-Host "Building email_notifier_layer..."
New-Item -ItemType Directory -Path "$BUILD_DIR\email_notifier_layer\python" -Force | Out-Null
pip install -r instabot_email_notifier\requirements.txt -t "$BUILD_DIR\email_notifier_layer\python" --platform manylinux2014_x86_64 --only-binary=:all:
Set-Location "$BUILD_DIR\email_notifier_layer"
Compress-Archive -Path python -DestinationPath "..\email_notifier_layer.zip" -Force
Set-Location ..\..

# List artifacts
Write-Host "========================================" -ForegroundColor Cyan
Write-Host "Build Artifacts:" -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan
Get-ChildItem -Path "$BUILD_DIR\*.zip" | Format-Table Name, Length

# Upload to S3
Write-Host ""
$upload = Read-Host "Upload artifacts to S3 bucket $S3Bucket? (y/n)"
if ($upload -eq 'y' -or $upload -eq 'Y') {
    Write-Host "Uploading to S3..." -ForegroundColor Yellow
    aws s3 cp "$BUILD_DIR\instabot_main.zip" "s3://$S3Bucket/"
    aws s3 cp "$BUILD_DIR\instabot_sqs_lambda.zip" "s3://$S3Bucket/"
    aws s3 cp "$BUILD_DIR\instabot_search_engine.zip" "s3://$S3Bucket/"
    aws s3 cp "$BUILD_DIR\instabot_email_notifier.zip" "s3://$S3Bucket/"
    aws s3 cp "$BUILD_DIR\main_layer.zip" "s3://$S3Bucket/"
    aws s3 cp "$BUILD_DIR\sqs_layer.zip" "s3://$S3Bucket/"
    aws s3 cp "$BUILD_DIR\search_engine_py_layer.zip" "s3://$S3Bucket/"
    aws s3 cp "$BUILD_DIR\email_notifier_layer.zip" "s3://$S3Bucket/"
    Write-Host "Upload complete!" -ForegroundColor Green
} else {
    Write-Host "Skipping S3 upload."
}

Write-Host ""
Write-Host "========================================" -ForegroundColor Green
Write-Host "Build Complete!" -ForegroundColor Green
Write-Host "========================================" -ForegroundColor Green

