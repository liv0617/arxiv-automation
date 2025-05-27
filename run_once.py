"""
Script to run the arXiv paper automation once for testing.
"""

import os
import sys
from datetime import datetime, timedelta
from dotenv import load_dotenv
from modules.arxiv import ArxivClient  # Use the improved arXiv client
from modules.api_clients import AnthropicClient
from modules.summarizer import PaperSummarizer
from modules.recommender import PaperRecommender
from modules.email_sender import EmailSender
from config import Config

def main():
    """Run the arXiv paper automation once."""
    # Check if today is a weekday (Monday=0, Sunday=6)
    today = datetime.now()
    if today.weekday() >= 5:  # Saturday=5, Sunday=6
        print(f"Skipping execution - today is {today.strftime('%A')} (weekend)")
        return
    
    print(f"Running on {today.strftime('%A, %B %d, %Y')}")
    
    # Load environment variables from .env file if it exists
    load_dotenv()
    
    # Create configuration
    config = Config()
    
    # Get arxiv configuration including cache settings
    arxiv_config = config.get_arxiv_config()
    
    # Create ArXiv client using the improved client with cache
    arxiv_client = ArxivClient(cache_dir=arxiv_config['cache_dir'])
    
    # Create Anthropic API client
    api_config = config.get_api_config()
    
    # Check for API key
    if not api_config["api_key"]:
        print("Error: ANTHROPIC_API_KEY not set in environment variables")
        sys.exit(1)
        
    # Create the client
    api_client = AnthropicClient(api_config["model"], api_config["api_key"])
    llm_provider = "anthropic"  # Hardcode to anthropic
    
    # Create paper summarizer with cache support
    summarizer = PaperSummarizer(api_client, arxiv_client)
    
    # Create paper recommender only if user interests are configured
    recommender = None
    if arxiv_config.get('user_interests') and arxiv_config['user_interests'].strip():
        recommender = PaperRecommender(api_client, arxiv_config['user_interests'])
    
    # Create email sender
    sendgrid_api_key = os.environ.get("SENDGRID_API_KEY")
    sender_email = os.environ.get("SENDER_EMAIL")
    recipient_email = os.environ.get("RECIPIENT_EMAIL")
    
    if not sendgrid_api_key:
        print("Error: SENDGRID_API_KEY not set in environment variables")
        sys.exit(1)
        
    if not sender_email:
        print("Error: SENDER_EMAIL not set in environment variables")
        sys.exit(1)
        
    if not recipient_email:
        print("Error: RECIPIENT_EMAIL not set in environment variables")
        sys.exit(1)
    
    email_sender = EmailSender(
        api_key=sendgrid_api_key,
        sender_email=sender_email
    )
    
    # Get search configuration and perform search
    print(f"Performing search with terms: {arxiv_config['search_terms']} in categories: {arxiv_config['categories']}")
    specialized_results = arxiv_client.search_papers(
        search_terms=arxiv_config['search_terms'],
        categories=arxiv_config['categories'],
        max_results=arxiv_config['max_results']
    )
    
    if specialized_results:
        print(f"✓ Found {len(specialized_results)} papers with search")
        for i, paper in enumerate(specialized_results):
            print(f"  Paper {i+1}: {paper.title}")
            print(f"    Published: {paper.published}")
            print(f"    PDF URL: {paper.pdf_url}")
            print(f"    Categories: {paper.categories}")
            print()
        
        # Use these results for our test
        search_results = specialized_results
    else:
        # Initialize search_results as empty list when no papers found
        search_results = []
    
    # If we have search results, optionally get recommendations before summarizing
    if search_results:
        if recommender:
            print("\nGetting paper recommendations based on your interests...")
            recommended_papers = recommender.recommend_papers(search_results)
            
            if recommended_papers:
                print(f"✓ {len(recommended_papers)} papers recommended out of {len(search_results)} total")
                for i, paper in enumerate(recommended_papers):
                    print(f"  Recommended Paper {i+1}: {paper.title}")
                
                print("\nSummarizing recommended papers with Claude using PDFs...")
                paper_summaries = summarizer.summarize_papers(recommended_papers)
            else:
                print("✗ No papers were recommended based on your interests")
                paper_summaries = []
        else:
            print("\nNo user interests configured, summarizing all papers...")
            paper_summaries = summarizer.summarize_papers(search_results)
        
        if paper_summaries:
            print(f"✓ Successfully summarized {len(paper_summaries)} papers")
            
            # Try to send an email with the summaries
            print(f"\nSending email to {recipient_email}...")
            today = datetime.now().strftime("%Y-%m-%d")
            subject = f"arXiv Papers ({today})"
            
            email_success = email_sender.send_email(
                recipient_email=recipient_email,
                subject=subject,
                paper_summaries=paper_summaries
            )
            
            if email_success:
                print("✓ Email sent successfully!")
            else:
                print("✗ Failed to send email")
        else:
            print("✗ Failed to generate paper summaries")
    else:
        print("\nNo papers found to summarize.")
    
    print("Test run completed.")

if __name__ == "__main__":
    main()