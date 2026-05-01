# MongoDB Deployment Guide

## Quick Setup

### 1. Install Dependencies
```bash
pip install flask flask-login pymongo dnspython bcrypt google-genai
```

### 2. Setup MongoDB

**Option A: Local MongoDB**
```bash
# Install MongoDB locally and it will run on mongodb://localhost:27017/
```

**Option B: MongoDB Atlas (Free Cloud)**
1. Go to https://www.mongodb.com/cloud/atlas
2. Create free account
3. Create a free cluster
4. Get connection string (looks like: `mongodb+srv://username:password@cluster.mongodb.net/`)
5. Set environment variable:
   ```bash
   set MONGO_URI=mongodb+srv://username:password@cluster.mongodb.net/
   ```

### 3. Run the App

**Rename the new MongoDB app:**
```bash
# Backup old app
move app.py app_old.py

# Use MongoDB version
move app_mongo.py app.py
```

**Start the server:**
```bash
python app.py
```

Visit: http://127.0.0.1:5000

## Environment Variables

Set these before running:

```bash
# Windows
set MONGO_URI=mongodb+srv://your-connection-string
set SECRET_KEY=your-random-secret-key
set GEMINI_API_KEY=your-gemini-api-key

# Linux/Mac
export MONGO_URI=mongodb+srv://your-connection-string
export SECRET_KEY=your-random-secret-key
export GEMINI_API_KEY=your-gemini-api-key
```

## Deploy to Cloud

### Render.com (Recommended)

1. Push code to GitHub
2. Go to https://render.com
3. Create new Web Service
4. Connect your GitHub repo
5. Set environment variables:
   - `MONGO_URI` = your MongoDB Atlas connection string
   - `SECRET_KEY` = random string
   - `GEMINI_API_KEY` = your API key
6. Deploy!

### Railway.app

1. Push code to GitHub
2. Go to https://railway.app
3. New Project → Deploy from GitHub
4. Add MongoDB plugin (or use Atlas)
5. Set environment variables
6. Deploy!

## Files Changed

- `requirements.txt` - Updated for MongoDB
- `models_mongo.py` - New MongoDB models
- `parser_mongo.py` - New MongoDB parser
- `app_mongo.py` - New MongoDB app (rename to app.py)

## Migration from SQLite

Your old SQLite data won't transfer automatically. You'll start fresh with MongoDB. If you need to keep old data, export it first.

## Benefits of MongoDB

✅ Easy cloud deployment
✅ Free tier on MongoDB Atlas
✅ No migration files needed
✅ Scales better
✅ Works on all platforms (Render, Railway, Vercel, etc.)
