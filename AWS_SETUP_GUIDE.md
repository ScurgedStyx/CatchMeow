# AWS S3 Voice Recorder Setup Guide

## Prerequisites

1. **AWS Account**: You need an AWS account with S3 access
2. **S3 Bucket**: Create an S3 bucket for storing voice recordings
3. **AWS Credentials**: Set up AWS access keys

## How to Get AWS Information

### Step 1: Create AWS Account
1. Go to [AWS Console](https://aws.amazon.com/)
2. Sign up for a free account if you don't have one
3. Complete the verification process

### Step 2: Create S3 Bucket
1. In AWS Console, search for "S3" and open S3 service
2. Click "Create bucket"
3. Choose a unique bucket name (e.g., `voice-recordings-yourname-12345`)
4. Select your preferred AWS region (e.g., `us-east-1`)
5. Keep default settings and click "Create bucket"
6. **Save your bucket name** - you'll need it later

### Step 3: Get AWS Access Keys
1. In AWS Console, click on your username (top right)
2. Click "Security credentials"
3. Scroll down to "Access keys" section
4. Click "Create access key"
5. Choose "Application running outside AWS"
6. Click "Next" and then "Create access key"
7. **IMPORTANT**: Copy both:
   - **Access Key ID** (starts with AKIA...)
   - **Secret Access Key** (long random string)
   - **Save these immediately** - you can't see the secret key again!

### Step 4: Get Mistral API Key
1. Go to [Mistral AI Console](https://console.mistral.ai/)
2. Sign up/login to your account
3. Go to "API Keys" section
4. Create a new API key
5. **Copy and save the API key**

## Setup Instructions

### 1. Set Environment Variables

**Windows (PowerShell):**
```powershell
$env:AWS_ACCESS_KEY_ID="AKIA..." # Your access key from Step 3
$env:AWS_SECRET_ACCESS_KEY="your-secret-key" # Your secret key from Step 3
$env:AWS_REGION="us-east-1" # Your bucket region from Step 2
$env:S3_BUCKET_NAME="your-bucket-name" # Your bucket name from Step 2
$env:MISTRAL_API_KEY="your-mistral-key" # Your Mistral key from Step 4
```

**Linux/Mac:**
```bash
export AWS_ACCESS_KEY_ID="AKIA..." # Your access key from Step 3
export AWS_SECRET_ACCESS_KEY="your-secret-key" # Your secret key from Step 3
export AWS_REGION="us-east-1" # Your bucket region from Step 2
export S3_BUCKET_NAME="your-bucket-name" # Your bucket name from Step 2
export MISTRAL_API_KEY="your-mistral-key" # Your Mistral key from Step 4
```

### 2. Install Dependencies

```bash
# Install Python dependencies
pip install boto3 requests mistralai

# Or use uv if you prefer
uv add boto3 requests mistralai
```

### 4. Run the MCP Server

```bash
python main.py
```

### 5. Open the Voice Recorder

Open `voice_recorder_s3.html` in your browser and make sure the MCP Server URL is set correctly (default: http://localhost:3000)

## Workflow

1. **Record Audio**: Click "Start Recording" → record your voice → click "Stop Recording"
2. **Upload to S3**: Click "Upload to S3" - this will:
   - Get a presigned URL from your MCP server
   - Upload the audio file directly to S3
   - Return the S3 public URL
3. **Transcribe**: Click "Transcribe Audio" to transcribe the uploaded audio using Mistral's Voxtral model

## MCP Tools Available

1. **generate_upload_url**: Generates presigned URLs for S3 uploads
2. **list_recordings**: Lists all recordings in your S3 bucket
3. **transcribe_s3_audio**: Transcribes audio files stored in S3
4. **transcribe_audio_url**: Transcribes any audio file from a URL

## Usage with Le Chat

Once your audio is uploaded to S3, you can use the public S3 URL with Le Chat:

1. Upload your recording to S3 using the voice recorder
2. Copy the S3 URL that gets generated
3. In Le Chat, you can reference this URL for transcription or analysis
4. Or use the MCP tools directly in Le Chat if it supports MCP integration

## Troubleshooting

- Make sure your AWS credentials have S3 permissions
- Check that your S3 bucket exists and is accessible
- Verify the MCP server is running on the correct port
- Ensure CORS is properly configured if accessing from a different domain