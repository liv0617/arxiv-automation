# arXiv Paper Automation

An automated tool that searches for papers on arXiv, intelligently recommends relevant ones based on your research interests, summarizes them using Claude, and sends daily email digests.

*(Note: This project, including this README, was assembled through pure vibes and cosmic intuition. I/Claude coded first and asked questions later. The git history reads like jazz improvisation. May the programming gods have mercy on our souls. ✨)*

## Features

- **Configurable Search**: Searches arXiv with customizable search terms and categories
- **Intelligent Recommendations**: Optional LLM-based filtering to recommend papers based on your research interests
- **Duplicate Detection**: Tracks previously seen papers to avoid sending duplicates
- **AI Summarization**: Uses Anthropic's Claude to generate comprehensive summaries from paper PDFs
- **Email Digests**: Sends well-formatted HTML emails with paper summaries via SendGrid
- **GitHub Actions Integration**: Automated daily runs at 4:00 PM UTC
- **Manual Execution**: Can be run on-demand for testing
- **Caching**: Paper summaries are cached to avoid reprocessing

## How It Works

1. **Search**: Searches arXiv using configurable search terms and categories (default: mechanistic interpretability papers)
2. **Filter Duplicates**: Removes previously seen papers (tracked in `seen_papers.json`)
3. **Intelligent Recommendations** (Optional): If `user_interests` is configured, uses Claude to analyze paper abstracts and recommend only the most relevant papers based on your research interests
4. **Summarization**: Downloads and analyzes PDFs using Claude to extract:
   - Concise summary (250-300 words)
   - Key methodologies
   - Main contributions
   - Notable limitations
5. **Email Digest**: Sends an HTML-formatted email with summaries (only recommended papers if using recommendations)

## Setup

### Prerequisites

- Python 3.11+
- Anthropic API key (for Claude)
- SendGrid API key (for email delivery)
- GitHub repository (for automated runs)

### Installation

1. Clone the repository:
   ```bash
   git clone https://github.com/yourusername/arxiv-automation.git
   cd arxiv-automation
   ```

2. Create a virtual environment:
   ```bash
   python -m venv arxiv-env
   source arxiv-env/bin/activate  # On Windows: arxiv-env\Scripts\activate
   ```

3. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```

### GitHub Actions Setup

1. Go to your repository Settings → Secrets and variables → Actions
2. Add the following secrets:
   - `ANTHROPIC_API_KEY`
   - `SENDGRID_API_KEY`
   - `SENDER_EMAIL`
   - `RECIPIENT_EMAIL`

3. The workflow will run automatically at 4:00 PM UTC daily, or can be triggered manually from the Actions tab

## Usage

### Manual Run (Testing)

```bash
python run_once.py
```

This will:
- Search for recent papers based on your configured search terms and categories
- Optionally filter papers using intelligent recommendations (if `user_interests` is set)
- Generate summaries for recommended/all papers found
- Send an email to the configured recipient
- Update `seen_papers.json` to track processed papers

### Automated Daily Runs

The GitHub Actions workflow (`.github/workflows/daily-arxiv.yml`) handles:
- Daily execution at 4:00 PM UTC
- Automatic commit of `seen_papers.json` to track processed papers
- Environment variable management from GitHub Secrets

## Configuration

Edit `config.json` to customize:

```json
{
  "llm_provider": "anthropic",
  "anthropic_model": "claude-opus-4-20250514",
  "search_terms": ["interpretability", "mechanistic interpretability"],
  "categories": ["cs.AI", "cs.LG", "cs.CL"],
  "max_results": 5,
  "cache_dir": "paper_cache",
  "run_time": "16:00",
  "user_interests": "I am interested in mechanistic interpretability research, particularly work on sparse features and circuits, feature manifolds, geometry of representations, and attention."
}
```

### Configuration Options

- **`search_terms`**: List of search terms to look for in papers
- **`categories`**: arXiv categories to search in (e.g., "cs.AI", "cs.LG", "cs.CL")
- **`max_results`**: Maximum number of papers to retrieve per run
- **`user_interests`** (Optional): Description of your research interests for intelligent recommendations
  - If set: Only papers recommended by Claude based on your interests will be summarized
  - If empty/missing: All retrieved papers will be summarized (original behavior)
- **`cache_dir`**: Directory to cache paper summaries
- **`run_time`**: Time for automated runs (24-hour format)

## Project Structure

```
├── modules/              # Core functionality
│   ├── arxiv.py         # arXiv API client with deduplication
│   ├── api_clients.py   # Anthropic Claude client
│   ├── recommender.py   # Intelligent paper recommendation system
│   ├── summarizer.py    # PDF analysis and summarization
│   └── email_sender.py  # SendGrid email formatting/sending
├── tests/               # Test suite
│   ├── test_config.py
│   ├── test_recommender.py
│   └── ...
├── run_once.py          # Manual execution script
├── config.py            # Configuration management
├── config.json          # Configuration file
├── seen_papers.json     # Tracking file for processed papers
├── paper_cache/         # Cached paper summaries
├── requirements.txt     # Python dependencies
├── .env.example         # Environment variables template
└── .github/
    └── workflows/
        └── daily-arxiv.yml  # GitHub Actions workflow
```

## Intelligent Recommendations

When `user_interests` is configured, the system uses a two-stage process:

1. **Abstract Analysis**: All retrieved paper abstracts are sent to Claude along with your research interests
2. **Relevance Scoring**: Claude rates each paper's relevance (1-5 scale) and recommends only papers scoring 4-5
3. **Selective Processing**: Only recommended papers proceed to PDF summarization

This saves API costs by avoiding expensive PDF analysis on irrelevant papers while ensuring you only receive highly relevant content.

## How Summarization Works

The tool sends paper PDFs directly to Claude using Anthropic's document analysis capabilities. For each paper, Claude extracts:

- **Summary**: A comprehensive 250-300 word overview focusing on your research interests
- **Methods**: Key methodologies and techniques used
- **Contributions**: Main contributions to the field
- **Limitations**: Any notable limitations mentioned by the authors

## Troubleshooting

**No papers found**: 
- Check your search terms and categories in `config.json`
- Verify there are new papers in the last day matching your criteria
- Review `seen_papers.json` - you may need to clear it to reprocess papers

**No papers recommended**:
- Your `user_interests` may be too specific - try broadening the description
- Check that abstracts contain relevant keywords related to your interests
- Consider temporarily removing `user_interests` to see all available papers

**Email not sending**:
- Verify SendGrid API key and email addresses in `.env`
- Check SendGrid account status and sending limits
- Ensure sender email is verified in SendGrid

**GitHub Actions failing**:
- Check that all required secrets are set in repository settings
- Review the Actions log for specific error messages
- Ensure `seen_papers.json` can be committed (check branch protection rules)

## Notes

- Only new papers are processed - previously seen papers are skipped
- The `seen_papers.json` file is automatically maintained and committed by GitHub Actions
- Paper summaries are cached in `paper_cache/` to avoid reprocessing
- When using recommendations, the system analyzes abstracts first (cheap) before PDF summarization (expensive)
- Set `user_interests` to empty string `""` to disable recommendations and process all papers
