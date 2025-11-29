#!/bin/bash

# Manual Build Script for InstaBot
# This script mimics the CodeBuild process locally for testing

set -e

echo "========================================"
echo "InstaBot Manual Build Script"
echo "========================================"

# Configuration
S3_BUCKET=${1:-"your-s3-bucket-name"}
BUILD_DIR="build-output"

if [ "$S3_BUCKET" = "your-s3-bucket-name" ]; then
    echo "ERROR: Please provide S3 bucket name"
    echo "Usage: ./manual-build.sh <s3-bucket-name>"
    exit 1
fi

echo "S3 Bucket: $S3_BUCKET"
echo "Build Directory: $BUILD_DIR"
echo ""

# Clean up
echo "Cleaning up previous builds..."
rm -rf "$BUILD_DIR"
mkdir -p "$BUILD_DIR"

# Package Lambda Functions
echo "========================================"
echo "Packaging Lambda Functions..."
echo "========================================"

echo "Packaging instabot_main..."
cd instabot_main
zip -r "../$BUILD_DIR/instabot_main.zip" lambda_function.py
cd ..

echo "Packaging instabot_sqs_lambda..."
cd instabot_sqs_lambda
zip -r "../$BUILD_DIR/instabot_sqs_lambda.zip" lambda_function.py
cd ..

echo "Packaging instabot_search_engine..."
cd instabot_search_engine
zip -r "../$BUILD_DIR/instabot_search_engine.zip" lambda_function.py
cd ..

echo "Packaging instabot_email_notifier..."
cd instabot_email_notifier
zip -r "../$BUILD_DIR/instabot_email_notifier.zip" lambda_function.py
cd ..

# Build Lambda Layers
echo "========================================"
echo "Building Lambda Layers..."
echo "========================================"

echo "Building main_layer..."
mkdir -p "$BUILD_DIR/main_layer/python"
pip install -r instabot_main/requirements.txt -t "$BUILD_DIR/main_layer/python" --platform manylinux2014_x86_64 --only-binary=:all:
cd "$BUILD_DIR/main_layer"
zip -r ../main_layer.zip python
cd ../..

echo "Building sqs_layer..."
mkdir -p "$BUILD_DIR/sqs_layer/python"
pip install -r instabot_sqs_lambda/requirements.txt -t "$BUILD_DIR/sqs_layer/python" --platform manylinux2014_x86_64 --only-binary=:all:
cd "$BUILD_DIR/sqs_layer"
zip -r ../sqs_layer.zip python
cd ../..

echo "Building search_engine_py_layer..."
mkdir -p "$BUILD_DIR/search_engine_py_layer/python"
pip install -r instabot_search_engine/requirements.txt -t "$BUILD_DIR/search_engine_py_layer/python" --platform manylinux2014_x86_64 --only-binary=:all:
cd "$BUILD_DIR/search_engine_py_layer"
zip -r ../search_engine_py_layer.zip python
cd ../..

echo "Building email_notifier_layer..."
mkdir -p "$BUILD_DIR/email_notifier_layer/python"
pip install -r instabot_email_notifier/requirements.txt -t "$BUILD_DIR/email_notifier_layer/python" --platform manylinux2014_x86_64 --only-binary=:all:
cd "$BUILD_DIR/email_notifier_layer"
zip -r ../email_notifier_layer.zip python
cd ../..

# List artifacts
echo "========================================"
echo "Build Artifacts:"
echo "========================================"
ls -lh "$BUILD_DIR"/*.zip

# Upload to S3
echo ""
read -p "Upload artifacts to S3 bucket $S3_BUCKET? (y/n): " -n 1 -r
echo
if [[ $REPLY =~ ^[Yy]$ ]]; then
    echo "Uploading to S3..."
    aws s3 cp "$BUILD_DIR/instabot_main.zip" "s3://$S3_BUCKET/"
    aws s3 cp "$BUILD_DIR/instabot_sqs_lambda.zip" "s3://$S3_BUCKET/"
    aws s3 cp "$BUILD_DIR/instabot_search_engine.zip" "s3://$S3_BUCKET/"
    aws s3 cp "$BUILD_DIR/instabot_email_notifier.zip" "s3://$S3_BUCKET/"
    aws s3 cp "$BUILD_DIR/main_layer.zip" "s3://$S3_BUCKET/"
    aws s3 cp "$BUILD_DIR/sqs_layer.zip" "s3://$S3_BUCKET/"
    aws s3 cp "$BUILD_DIR/search_engine_py_layer.zip" "s3://$S3_BUCKET/"
    aws s3 cp "$BUILD_DIR/email_notifier_layer.zip" "s3://$S3_BUCKET/"
    echo "Upload complete!"
else
    echo "Skipping S3 upload."
fi

echo ""
echo "========================================"
echo "Build Complete!"
echo "========================================"

