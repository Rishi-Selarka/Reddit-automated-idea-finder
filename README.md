# 🚀 Reddit iOS Idea Finder

An automated Python workflow that scrapes Reddit for iOS app ideas and sends you beautifully formatted daily email summaries powered by GPT-4o-mini.

## ✨ Features

### Core Functionality
- **Multi-Subreddit Scraping**: Monitors 12 relevant subreddits including r/AppIdeas, r/iOSProgramming, r/SwiftUI, and more
- **Smart Filtering**: Uses keyword matching to find relevant iOS app ideas
- **AI-Powered Summaries**: GPT-4o-mini transforms Reddit posts into structured app concepts
- **Beautiful HTML Emails**: Professional email templates with idea cards and metadata
- **Daily Automation**: GitHub Actions runs the workflow automatically every day

### Enhanced Features (Beyond Original Plan)
- **Intelligent Scoring**: Advanced algorithm considers upvotes, comments, recency, and subreddit relevance
- **Deduplication**: Removes duplicate posts based on content similarity
- **Comprehensive Analysis**: Each idea includes problem, solution, target audience, monetization, and feasibility
- **Market Insights**: Provides market potential and technical difficulty ratings
- **Rich Metadata**: Shows upvotes, comments, subreddit, and Reddit links
- **Error Handling**: Robust error handling and logging throughout

## 🛠️ Setup Instructions

### 1. Clone and Install
```bash
git clone <your-repo>
cd iOS_Idea_Finder
pip install -r requirements.txt
```

### 2. Get API Credentials

#### Reddit API (Free)
1. Go to https://www.reddit.com/prefs/apps
2. Click "Create App" or "Create Another App"
3. Choose "script" as the app type
4. Copy the client ID and secret

#### OpenAI API
1. Go to https://platform.openai.com/api-keys
2. Create a new API key
3. Copy the key (starts with `sk-`)

#### Gmail App Password
1. Enable 2FA on your Gmail account
2. Go to Google Account settings → Security → App passwords
3. Generate a new app password for "Mail"
4. Use this password (not your regular Gmail password)

### 3. Configure Environment Variables

Create a `.env` file based on `env_example.txt`:
```bash
cp env_example.txt .env
# Edit .env with your actual credentials
```

### 4. Test Locally
```bash
python reddit_idea_finder.py
```

### 5. Set Up GitHub Actions (Optional)

1. Push your code to GitHub
2. Add secrets in GitHub repository settings:
   - `REDDIT_CLIENT_ID`
   - `REDDIT_CLIENT_SECRET` 
   - `OPENAI_API_KEY`
   - `EMAIL_SENDER`
   - `EMAIL_PASSWORD`
   - `EMAIL_RECEIVER`
3. The workflow will run daily at 6:00 AM UTC

## 📊 How It Works

### 1. Data Collection
- Scrapes 12 subreddits for posts from the last 3 days
- Filters posts containing iOS/app-related keywords
- Collects metadata: upvotes, comments, subreddit, etc.

### 2. Intelligent Scoring
Each post gets a relevance score based on:
- **Upvotes** (30%): Popular posts get higher scores
- **Comments** (20%): Engagement indicates interest
- **Keyword Matches** (25%): More relevant keywords = higher score
- **Recency** (15%): Newer posts prioritized
- **Subreddit Relevance** (10%): r/AppIdeas scores higher than r/iPhone

### 3. AI Processing
GPT-4o-mini analyzes each post and generates:
- Problem statement
- App solution concept
- Target audience
- Unique features
- Monetization strategy
- Technical feasibility (Easy/Medium/Hard)
- Market potential (Small/Medium/Large)

### 4. Email Generation
Creates beautiful HTML emails with:
- Idea cards with structured information
- Reddit metadata and links
- Visual indicators for feasibility and market size
- Daily statistics summary

## 🎯 Monitored Subreddits

| Subreddit | Relevance Score | Focus |
|-----------|----------------|-------|
| r/AppIdeas | 1.0 | Pure app ideas |
| r/SomebodyMakeThis | 0.9 | Product requests |
| r/Lightbulb | 0.8 | Creative ideas |
| r/iOSProgramming | 0.7 | iOS development |
| r/SwiftUI | 0.7 | SwiftUI development |
| r/SideProject | 0.6 | Side projects |
| r/entrepreneur | 0.5 | Business ideas |
| r/startups | 0.5 | Startup concepts |

## 📧 Sample Email Output

Each daily email contains:
- **Header**: Date and generation info
- **Statistics**: Number of ideas, total upvotes, subreddits covered
- **5 Idea Cards**: Each with:
  - Original Reddit post title and metadata
  - AI-generated problem statement
  - App solution concept
  - Target audience
  - Unique features
  - Monetization strategy
  - Feasibility and market potential badges
  - Direct link to Reddit post

## 🔧 Customization

### Add More Subreddits
Edit the `subreddits` list in `reddit_idea_finder.py`:
```python
self.subreddits = [
    'AppIdeas', 'iOSProgramming', 'SideProject', 'SwiftUI',
    'YourNewSubreddit'  # Add here
]
```

### Adjust Keywords
Modify the `keywords` list to catch different types of posts:
```python
self.keywords = [
    'app idea', 'wish there was an app', 'ios app',
    'your custom keyword'  # Add here
]
```

### Change Scoring Weights
Adjust the `scoring_weights` dictionary to prioritize different factors:
```python
self.scoring_weights = {
    'upvotes': 0.4,      # Increase upvote importance
    'comments': 0.1,     # Decrease comment importance
    # ... etc
}
```

## 🚨 Troubleshooting

### Common Issues

**"No posts found"**
- Check if Reddit API credentials are correct
- Verify subreddit names are spelled correctly
- Try running during peak Reddit hours (evening US time)

**"OpenAI API error"**
- Verify your API key is valid and has credits
- Check if you've hit rate limits
- Ensure you're using the correct model name

**"Email not sending"**
- Use Gmail App Password, not your regular password
- Check if 2FA is enabled on Gmail
- Verify SMTP settings

**"GitHub Actions failing"**
- Check that all secrets are set correctly
- Review workflow logs in GitHub Actions tab
- Ensure Python version matches requirements

## 📈 Future Enhancements

Potential improvements you could add:
- **Web Dashboard**: View ideas in a web interface
- **Idea Tracking**: Mark ideas as "building" or "completed"
- **Trending Analysis**: Track which types of ideas are popular
- **Slack Integration**: Send ideas to Slack instead of email
- **Database Storage**: Store ideas for historical analysis
- **Mobile App**: Native iOS app to view ideas on the go

## 🤝 Contributing

Feel free to submit issues, feature requests, or pull requests to improve the Reddit iOS Idea Finder!

## 📄 License

MIT License - feel free to use this for your own projects!

---

**Happy idea hunting! 🎯**
