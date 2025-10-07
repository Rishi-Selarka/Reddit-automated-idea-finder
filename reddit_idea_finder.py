#!/usr/bin/env python3
"""
Reddit iOS Idea Finder - Automated Daily Email Workflow
Enhanced version with scoring, deduplication, and trending analysis
"""

import os
import praw
import openai
import smtplib
import logging
from datetime import datetime, timedelta
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from dotenv import load_dotenv
import re
from collections import defaultdict
import hashlib
from typing import List, Dict, Tuple
import json

# Load environment variables
load_dotenv()

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class RedditIdeaFinder:
    def __init__(self):
        # Initialize Reddit API
        self.reddit = praw.Reddit(
            client_id=os.getenv('REDDIT_CLIENT_ID'),
            client_secret=os.getenv('REDDIT_CLIENT_SECRET'),
            user_agent='iOS_Idea_Finder/1.0'
        )
        
        # Initialize OpenAI
        openai.api_key = os.getenv('OPENAI_API_KEY')
        self.client = openai.OpenAI(api_key=os.getenv('OPENAI_API_KEY'))
        
        # Configuration
        self.subreddits = [
            'AppIdeas', 'iOSProgramming', 'SideProject', 'SwiftUI',
            'entrepreneur', 'startups', 'SomebodyMakeThis', 'Lightbulb',
            'appdev', 'mobile', 'iPhone', 'iPad'
        ]
        
        self.keywords = [
            'app idea', 'wish there was an app', 'ios app', 'side project',
            'build this', 'someone should make', 'app concept', 'mobile app',
            'iphone app', 'ipad app', 'swift app', 'swiftui app'
        ]
        
        # Scoring weights
        self.scoring_weights = {
            'upvotes': 0.3,
            'comments': 0.2,
            'keyword_matches': 0.25,
            'recency': 0.15,
            'subreddit_relevance': 0.1
        }
        
        # Subreddit relevance scores
        self.subreddit_scores = {
            'AppIdeas': 1.0,
            'SomebodyMakeThis': 0.9,
            'Lightbulb': 0.8,
            'iOSProgramming': 0.7,
            'SwiftUI': 0.7,
            'SideProject': 0.6,
            'entrepreneur': 0.5,
            'startups': 0.5,
            'appdev': 0.6,
            'mobile': 0.5,
            'iPhone': 0.4,
            'iPad': 0.4
        }

    def fetch_posts(self, limit_per_subreddit: int = 25) -> List[Dict]:
        """Fetch posts from all subreddits and filter by keywords"""
        all_posts = []
        
        for subreddit_name in self.subreddits:
            try:
                logger.info(f"Fetching posts from r/{subreddit_name}")
                subreddit = self.reddit.subreddit(subreddit_name)
                
                # Get hot posts from the last 24 hours
                for post in subreddit.hot(limit=limit_per_subreddit):
                    # Skip if post is too old (more than 3 days)
                    post_age = datetime.now() - datetime.fromtimestamp(post.created_utc)
                    if post_age.days > 3:
                        continue
                    
                    # Check if post contains keywords
                    title_lower = post.title.lower()
                    selftext_lower = post.selftext.lower() if post.selftext else ""
                    
                    keyword_matches = sum(1 for keyword in self.keywords 
                                        if keyword in title_lower or keyword in selftext_lower)
                    
                    if keyword_matches > 0:
                        post_data = {
                            'id': post.id,
                            'title': post.title,
                            'selftext': post.selftext,
                            'url': f"https://reddit.com{post.permalink}",
                            'upvotes': post.score,
                            'comments': post.num_comments,
                            'subreddit': subreddit_name,
                            'created_utc': post.created_utc,
                            'keyword_matches': keyword_matches,
                            'author': str(post.author) if post.author else '[deleted]'
                        }
                        all_posts.append(post_data)
                        
            except Exception as e:
                logger.error(f"Error fetching from r/{subreddit_name}: {e}")
                continue
        
        logger.info(f"Found {len(all_posts)} posts with keywords")
        return all_posts

    def calculate_post_score(self, post: Dict) -> float:
        """Calculate a relevance score for each post"""
        # Normalize upvotes (log scale to handle viral posts)
        upvotes_score = min(10, max(0, post['upvotes'])) / 10
        
        # Normalize comments
        comments_score = min(5, max(0, post['comments'])) / 5
        
        # Keyword matches (already normalized)
        keyword_score = min(1.0, post['keyword_matches'] / 3)
        
        # Recency score (newer posts get higher scores)
        post_age_hours = (datetime.now() - datetime.fromtimestamp(post['created_utc'])).total_seconds() / 3600
        recency_score = max(0, 1 - (post_age_hours / 72))  # 72 hours = 0 score
        
        # Subreddit relevance
        subreddit_score = self.subreddit_scores.get(post['subreddit'], 0.3)
        
        # Calculate weighted score
        total_score = (
            upvotes_score * self.scoring_weights['upvotes'] +
            comments_score * self.scoring_weights['comments'] +
            keyword_score * self.scoring_weights['keyword_matches'] +
            recency_score * self.scoring_weights['recency'] +
            subreddit_score * self.scoring_weights['subreddit_relevance']
        )
        
        return total_score

    def deduplicate_posts(self, posts: List[Dict]) -> List[Dict]:
        """Remove duplicate posts based on content similarity"""
        seen_hashes = set()
        unique_posts = []
        
        for post in posts:
            # Create a hash based on title and first 100 chars of content
            content = f"{post['title']} {post['selftext'][:100]}".lower()
            content_hash = hashlib.md5(content.encode()).hexdigest()
            
            if content_hash not in seen_hashes:
                seen_hashes.add(content_hash)
                unique_posts.append(post)
        
        logger.info(f"Removed {len(posts) - len(unique_posts)} duplicate posts")
        return unique_posts

    def generate_idea_summary(self, post: Dict) -> Dict:
        """Use GPT-4o-mini to generate iOS app idea summary"""
        try:
            prompt = f"""
You are a creative iOS developer assistant. Analyze this Reddit post and transform it into a compelling iOS app idea.

Reddit Post:
Title: {post['title']}
Content: {post['selftext'][:1000]}...
Subreddit: r/{post['subreddit']}
Upvotes: {post['upvotes']}

Please provide a structured response in JSON format with these exact keys:
{{
    "problem": "Clear problem statement (max 50 words)",
    "solution": "Core app concept and how it solves the problem (max 80 words)",
    "target_audience": "Who would use this app (max 30 words)",
    "unique_features": "What makes this app unique or innovative (max 50 words)",
    "monetization": "Potential revenue model (max 30 words)",
    "feasibility": "Technical difficulty rating (Easy/Medium/Hard)",
    "market_potential": "Market size estimate (Small/Medium/Large)"
}}

Keep responses concise and focused on iOS development. Be creative but realistic.
"""

            response = self.client.chat.completions.create(
                model="gpt-4o-mini",
                messages=[
                    {"role": "system", "content": "You are an expert iOS developer and product strategist. Always respond with valid JSON only."},
                    {"role": "user", "content": prompt}
                ],
                max_tokens=500,
                temperature=0.7
            )
            
            # Parse JSON response
            summary_text = response.choices[0].message.content.strip()
            # Clean up the response to ensure it's valid JSON
            summary_text = re.sub(r'```json\n?', '', summary_text)
            summary_text = re.sub(r'\n?```', '', summary_text)
            
            summary = json.loads(summary_text)
            
            # Add metadata
            summary['reddit_url'] = post['url']
            summary['reddit_title'] = post['title']
            summary['subreddit'] = post['subreddit']
            summary['upvotes'] = post['upvotes']
            summary['comments'] = post['comments']
            summary['score'] = post.get('calculated_score', 0)
            
            return summary
            
        except Exception as e:
            logger.error(f"Error generating summary for post {post['id']}: {e}")
            return {
                "problem": "Error processing this idea",
                "solution": "Please check the original Reddit post for details",
                "target_audience": "Unknown",
                "unique_features": "Unknown",
                "monetization": "Unknown",
                "feasibility": "Unknown",
                "market_potential": "Unknown",
                "reddit_url": post['url'],
                "reddit_title": post['title'],
                "subreddit": post['subreddit'],
                "upvotes": post['upvotes'],
                "comments": post['comments'],
                "score": 0
            }

    def create_html_email(self, ideas: List[Dict], date: str) -> str:
        """Create a beautiful HTML email with the ideas"""
        html_template = f"""
<!DOCTYPE html>
<html>
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Daily iOS App Ideas</title>
    <style>
        body {{
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
            line-height: 1.6;
            color: #333;
            max-width: 800px;
            margin: 0 auto;
            padding: 20px;
            background-color: #f8f9fa;
        }}
        .header {{
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            color: white;
            padding: 30px;
            border-radius: 12px;
            text-align: center;
            margin-bottom: 30px;
        }}
        .header h1 {{
            margin: 0;
            font-size: 28px;
            font-weight: 600;
        }}
        .header p {{
            margin: 10px 0 0 0;
            opacity: 0.9;
            font-size: 16px;
        }}
        .idea-card {{
            background: white;
            border-radius: 12px;
            padding: 25px;
            margin-bottom: 25px;
            box-shadow: 0 4px 6px rgba(0, 0, 0, 0.1);
            border-left: 4px solid #667eea;
        }}
        .idea-header {{
            display: flex;
            justify-content: space-between;
            align-items: flex-start;
            margin-bottom: 15px;
        }}
        .idea-title {{
            font-size: 20px;
            font-weight: 600;
            color: #2c3e50;
            margin: 0;
            flex: 1;
        }}
        .idea-meta {{
            background: #e3f2fd;
            padding: 8px 12px;
            border-radius: 20px;
            font-size: 12px;
            color: #1976d2;
            white-space: nowrap;
            margin-left: 15px;
        }}
        .idea-section {{
            margin-bottom: 15px;
        }}
        .idea-section h4 {{
            color: #667eea;
            margin: 0 0 8px 0;
            font-size: 14px;
            font-weight: 600;
            text-transform: uppercase;
            letter-spacing: 0.5px;
        }}
        .idea-section p {{
            margin: 0;
            color: #555;
        }}
        .reddit-link {{
            display: inline-block;
            background: #ff4500;
            color: white;
            padding: 8px 16px;
            text-decoration: none;
            border-radius: 6px;
            font-size: 14px;
            font-weight: 500;
            margin-top: 15px;
        }}
        .reddit-link:hover {{
            background: #e03d00;
        }}
        .footer {{
            text-align: center;
            margin-top: 40px;
            padding: 20px;
            color: #666;
            font-size: 14px;
            border-top: 1px solid #eee;
        }}
        .stats {{
            background: #f8f9fa;
            padding: 15px;
            border-radius: 8px;
            margin-bottom: 20px;
            text-align: center;
        }}
        .stats-item {{
            display: inline-block;
            margin: 0 20px;
            text-align: center;
        }}
        .stats-number {{
            font-size: 24px;
            font-weight: 600;
            color: #667eea;
        }}
        .stats-label {{
            font-size: 12px;
            color: #666;
            text-transform: uppercase;
        }}
    </style>
</head>
<body>
    <div class="header">
        <h1>🚀 Daily iOS App Ideas</h1>
        <p>{date} • Generated from Reddit via GPT-4o-mini</p>
    </div>
    
    <div class="stats">
        <div class="stats-item">
            <div class="stats-number">{len(ideas)}</div>
            <div class="stats-label">Ideas Found</div>
        </div>
        <div class="stats-item">
            <div class="stats-number">{sum(idea.get('upvotes', 0) for idea in ideas)}</div>
            <div class="stats-label">Total Upvotes</div>
        </div>
        <div class="stats-item">
            <div class="stats-number">{len(set(idea.get('subreddit', '') for idea in ideas))}</div>
            <div class="stats-label">Subreddits</div>
        </div>
    </div>
"""

        for i, idea in enumerate(ideas, 1):
            feasibility_color = {
                'Easy': '#4caf50',
                'Medium': '#ff9800', 
                'Hard': '#f44336'
            }.get(idea.get('feasibility', 'Unknown'), '#666')
            
            market_color = {
                'Small': '#f44336',
                'Medium': '#ff9800',
                'Large': '#4caf50'
            }.get(idea.get('market_potential', 'Unknown'), '#666')

            html_template += f"""
    <div class="idea-card">
        <div class="idea-header">
            <h2 class="idea-title">{i}️⃣ {idea.get('reddit_title', 'Untitled')}</h2>
            <div class="idea-meta">
                r/{idea.get('subreddit', 'unknown')} • ⭐ {idea.get('upvotes', 0)} upvotes
            </div>
        </div>
        
        <div class="idea-section">
            <h4>🎯 Problem</h4>
            <p>{idea.get('problem', 'Not specified')}</p>
        </div>
        
        <div class="idea-section">
            <h4>💡 Solution</h4>
            <p>{idea.get('solution', 'Not specified')}</p>
        </div>
        
        <div class="idea-section">
            <h4>👥 Target Audience</h4>
            <p>{idea.get('target_audience', 'Not specified')}</p>
        </div>
        
        <div class="idea-section">
            <h4>✨ Unique Features</h4>
            <p>{idea.get('unique_features', 'Not specified')}</p>
        </div>
        
        <div class="idea-section">
            <h4>💰 Monetization</h4>
            <p>{idea.get('monetization', 'Not specified')}</p>
        </div>
        
        <div style="display: flex; gap: 15px; margin-top: 15px;">
            <div style="background: {feasibility_color}; color: white; padding: 4px 8px; border-radius: 4px; font-size: 12px;">
                Difficulty: {idea.get('feasibility', 'Unknown')}
            </div>
            <div style="background: {market_color}; color: white; padding: 4px 8px; border-radius: 4px; font-size: 12px;">
                Market: {idea.get('market_potential', 'Unknown')}
            </div>
        </div>
        
        <a href="{idea.get('reddit_url', '#')}" class="reddit-link" target="_blank">
            🔗 View on Reddit
        </a>
    </div>
"""

        html_template += """
    <div class="footer">
        <p>🤖 Generated automatically from Reddit via GPT-4o-mini</p>
        <p>💡 Want to build one of these ideas? Start coding!</p>
    </div>
</body>
</html>
"""
        return html_template

    def send_email(self, html_content: str, subject: str):
        """Send the HTML email via Gmail SMTP"""
        try:
            msg = MIMEMultipart('alternative')
            msg['Subject'] = subject
            msg['From'] = os.getenv('EMAIL_SENDER')
            msg['To'] = os.getenv('EMAIL_RECEIVER')
            
            # Add HTML part
            html_part = MIMEText(html_content, 'html')
            msg.attach(html_part)
            
            # Send email
            with smtplib.SMTP_SSL('smtp.gmail.com', 465) as server:
                server.login(os.getenv('EMAIL_SENDER'), os.getenv('EMAIL_PASSWORD'))
                server.send_message(msg)
            
            logger.info("Email sent successfully!")
            
        except Exception as e:
            logger.error(f"Error sending email: {e}")
            raise

    def run(self):
        """Main execution method"""
        try:
            logger.info("Starting Reddit iOS Idea Finder...")
            
            # Fetch posts
            posts = self.fetch_posts()
            if not posts:
                logger.warning("No posts found with keywords")
                return
            
            # Calculate scores and sort
            for post in posts:
                post['calculated_score'] = self.calculate_post_score(post)
            
            # Sort by score and deduplicate
            posts.sort(key=lambda x: x['calculated_score'], reverse=True)
            unique_posts = self.deduplicate_posts(posts)
            
            # Take top 5 posts
            top_posts = unique_posts[:5]
            
            # Generate AI summaries
            logger.info("Generating AI summaries...")
            ideas = []
            for post in top_posts:
                summary = self.generate_idea_summary(post)
                ideas.append(summary)
            
            # Create and send email
            date_str = datetime.now().strftime("%B %d, %Y")
            subject = f"🚀 Daily iOS App Ideas from Reddit — {date_str}"
            
            html_content = self.create_html_email(ideas, date_str)
            self.send_email(html_content, subject)
            
            logger.info(f"Successfully processed and sent {len(ideas)} ideas!")
            
        except Exception as e:
            logger.error(f"Error in main execution: {e}")
            raise

def main():
    """Main function"""
    finder = RedditIdeaFinder()
    finder.run()

if __name__ == "__main__":
    main()
