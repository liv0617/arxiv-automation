"""Improved module for interacting with arXiv API using the arxiv package."""

from dataclasses import dataclass
import os
import json
import arxiv
from datetime import datetime
from typing import List, Dict, Optional, Set

@dataclass
class PaperData:
    id: str
    title: str
    url: str
    pdf_url: Optional[str] = None
    doi: Optional[str] = None
    comment: Optional[str] = None
    published: Optional[str] = None
    authors: Optional[List[str]] = None
    abstract: Optional[str] = None
    keywords: Optional[List[str]] = None
    summary: Optional[str] = None
    categories: Optional[List[str]] = None
    
    def to_dict(self) -> Dict:
        """Convert PaperData to dictionary for JSON serialization."""
        return {
            'id': self.id,
            'title': self.title,
            'url': self.url,
            'pdf_url': self.pdf_url,
            'doi': self.doi,
            'comment': self.comment,
            'published': self.published,
            'authors': self.authors,
            'abstract': self.abstract,
            'keywords': self.keywords,
            'summary': self.summary,
            'categories': self.categories
        }
    
    @classmethod
    def from_dict(cls, data: Dict) -> 'PaperData':
        """Create PaperData from dictionary."""
        return cls(**data)

class ArxivClient:
    """A client for interacting with the arXiv API with paper tracking."""
    
    SEEN_PAPERS_FILE = "seen_papers.json"
    
    def __init__(self, cache_dir: str = "paper_cache"):
        """Initialize the arXiv client."""
        self.client = arxiv.Client()
        self.seen_papers = self._load_seen_papers()
        self.cache_dir = cache_dir
        self._ensure_cache_dir()
    
    def _load_seen_papers(self) -> Dict[str, str]:
        """
        Load the list of previously seen papers from disk.
        
        Returns:
            Dict[str, str]: Map of paper ID to last seen date
        """
        if os.path.exists(self.SEEN_PAPERS_FILE):
            try:
                with open(self.SEEN_PAPERS_FILE, 'r') as f:
                    return json.load(f)
            except (json.JSONDecodeError, IOError):
                print(f"Warning: Error reading {self.SEEN_PAPERS_FILE}, starting fresh")
                return {}
        return {}
    
    def _save_seen_papers(self):
        """Save the list of seen papers to disk."""
        try:
            with open(self.SEEN_PAPERS_FILE, 'w') as f:
                json.dump(self.seen_papers, f)
        except IOError as e:
            print(f"Warning: Unable to save seen papers file: {e}")
    
    def mark_papers_as_seen(self, papers: List[Dict]):
        """
        Mark papers as seen to avoid duplicates in future searches.
        
        Args:
            papers: List of paper dictionaries
        """
        current_date = datetime.now().isoformat()
        for paper in papers:
            if paper:
                self.seen_papers[paper.id] = current_date
        self._save_seen_papers()
    
    def _ensure_cache_dir(self):
        """Ensure the cache directory exists."""
        from pathlib import Path
        Path(self.cache_dir).mkdir(exist_ok=True)
    
    def _get_cache_path(self, paper_id: str) -> str:
        """Get the cache file path for a paper ID."""
        return os.path.join(self.cache_dir, f"{paper_id}.json")
    
    def save_paper_to_cache(self, paper: PaperData):
        """Save a PaperData object to cache."""
        try:
            cache_path = self._get_cache_path(paper.id)
            with open(cache_path, 'w') as f:
                json.dump(paper.to_dict(), f, indent=2)
            print(f"Cached paper: {paper.id}")
        except Exception as e:
            print(f"Warning: Unable to cache paper {paper.id}: {e}")
    
    def load_paper_from_cache(self, paper_id: str) -> Optional[PaperData]:
        """Load a PaperData object from cache if it exists."""
        try:
            cache_path = self._get_cache_path(paper_id)
            if os.path.exists(cache_path):
                with open(cache_path, 'r') as f:
                    data = json.load(f)
                paper = PaperData.from_dict(data)
                print(f"Loaded paper from cache: {paper_id}")
                return paper
        except Exception as e:
            print(f"Warning: Unable to load paper {paper_id} from cache: {e}")
        return None
    
    def is_paper_cached(self, paper_id: str) -> bool:
        """Check if a paper is cached."""
        cache_path = self._get_cache_path(paper_id)
        return os.path.exists(cache_path)
    
    def _construct_query(self, search_terms: Optional[List[str]] = None, categories: Optional[List[str]] = None) -> str:
        """
        Construct an arXiv query string with proper URL encoding.
        
        Args:
            search_terms: List of search terms to search for
            categories: List of arXiv categories (e.g., ['cs.AI', 'cs.LG'])
            
        Returns:
            str: Properly formatted query string for arXiv API
        """
        query_parts = []
        
        # Add categories with OR between them
        if categories:
            if len(categories) > 1:
                cats = " OR ".join([f"cat:{cat}" for cat in categories])
                query_parts.append(f"({cats})")
            else:
                query_parts.append(f"cat:{categories[0]}")
        
        # Add search terms with proper encoding
        if search_terms:
            if len(search_terms) > 1:
                # For multiple terms, use OR and encode quotes as %22
                encoded_terms = []
                for term in search_terms:
                    if " " in term:  # Multi-word terms need quotes
                        encoded_terms.append(f'%22{term}%22')
                    else:
                        encoded_terms.append(term)
                terms_str = " OR ".join(encoded_terms)
                query_parts.append(f"({terms_str})")
            else:
                # Single term
                term = search_terms[0]
                if " " in term:  # Multi-word term needs quotes
                    query_parts.append(f'%22{term}%22')
                else:
                    query_parts.append(term)
        
        # Join query parts with AND
        return " AND ".join(query_parts) if query_parts else ""
    
    def search_papers(self, search_terms: Optional[List[str]] = None, categories: Optional[List[str]] = None, 
                     max_results: int = 10, request_size: int = 20, timeout_seconds: float = 1.0) -> List[PaperData]:
        """
        Generic search for papers with configurable terms and categories.
        Makes individual requests and checks for duplicates.
        Continues until we have enough new papers or exhaust the search space.
        
        Args:
            search_terms: List of search terms to search for
            categories: List of arXiv categories (e.g., ['cs.AI', 'cs.LG'])
            max_results: Maximum number of new papers to return
            request_size: Number of papers to fetch in each request to arXiv
            timeout_seconds: Time to wait between requests to be polite to arXiv
            
        Returns:
            List[PaperData]: List of paper data objects
        """
        import time
        
        # Construct the query
        query = self._construct_query(search_terms, categories)
        if not query:
            print("No search terms or categories provided")
            return []
            
        print(f"Searching arXiv with query: {query}")
        
        found_papers = []
        seen_in_this_run = set()
        start_index = 0
        consecutive_seen_requests = 0
        max_consecutive_seen = 3  # Stop if we see 3 consecutive requests with all seen papers
        
        while len(found_papers) < max_results and consecutive_seen_requests < max_consecutive_seen:
            print(f"Making request {start_index // request_size + 1} (papers {start_index}-{start_index + request_size - 1})")
            
            # Create a new search for this batch
            search = arxiv.Search(
                query=query,
                max_results=request_size,
                sort_by=arxiv.SortCriterion.SubmittedDate,
                sort_order=arxiv.SortOrder.Descending  # Most recent first
            )
            
            # Set the start index for this request
            search.offset = start_index
            
            try:
                # Fetch this batch of papers
                results = list(self.client.results(search))
                
                if not results:
                    print("No more papers available from arXiv")
                    break
                
                # Check if we found any new papers in this batch
                new_papers_in_batch = 0
                
                for paper in results:
                    paper_id = paper.entry_id.split('/')[-1]
                    
                    # Skip if we've already seen this paper before
                    if paper_id in self.seen_papers or paper_id in seen_in_this_run:
                        print(f"Skipping already seen paper: {paper.title}")
                        continue
                    
                    # Convert the paper to our format and add it to the results
                    paper_data = self._convert_result(paper)
                    found_papers.append(paper_data)
                    seen_in_this_run.add(paper_id)
                    new_papers_in_batch += 1
                    
                    print(f"Found new paper: {paper.title}")
                    
                    # Check if we have enough papers
                    if len(found_papers) >= max_results:
                        break
                
                # Track consecutive requests with no new papers
                if new_papers_in_batch == 0:
                    consecutive_seen_requests += 1
                    print(f"No new papers in this batch ({consecutive_seen_requests}/{max_consecutive_seen})")
                else:
                    consecutive_seen_requests = 0
                
                # Move to the next batch
                start_index += request_size
                
                # Wait between requests to be polite to arXiv
                if len(found_papers) < max_results and consecutive_seen_requests < max_consecutive_seen:
                    print(f"Waiting {timeout_seconds} seconds before next request...")
                    time.sleep(timeout_seconds)
                    
            except Exception as e:
                print(f"Error in request: {e}")
                break
        
        print(f"Search completed. Found {len(found_papers)} new papers.")
        
        # Mark all new papers as seen
        self.mark_papers_as_seen(found_papers)
        
        return found_papers
    
    def search_interpretability_papers(self, max_results: int = 10, request_size: int = 20, timeout_seconds: float = 1.0) -> List[PaperData]:
        """
        Search for interpretability papers, making individual requests and checking for duplicates.
        Continues until we have enough new papers or exhaust the search space.
        
        Args:
            max_results: Maximum number of new papers to return
            request_size: Number of papers to fetch in each request to arXiv
            timeout_seconds: Time to wait between requests to be polite to arXiv
            
        Returns:
            List[PaperData]: List of paper data objects
        """
        # Use the generic search function with interpretability-specific terms
        return self.search_papers(
            search_terms=["mechanistic interpretability"],
            categories=["cs.AI", "cs.LG", "cs.CL"],
            max_results=max_results,
            request_size=request_size,
            timeout_seconds=timeout_seconds
        )
    
    def search(self, search_terms=None, categories=None, max_results=10):
        """
        Search arXiv for papers matching the given criteria.
        
        Args:
            search_terms: Search terms or phrases
            categories: arXiv categories to search in
            max_results: Maximum number of results to return
            
        Returns:
            list: A list of dictionaries containing paper metadata
        """
        # Build a query string in the format from working_interp_search.py
        query_parts = []
        
        # Add categories with OR between them
        if categories:
            if isinstance(categories, list) and len(categories) > 0:
                cats = " OR ".join([f"cat:{cat}" for cat in categories])
                if len(categories) > 1:
                    query_parts.append(f"({cats})")
                else:
                    query_parts.append(cats)
        
        # Add search terms with quotes for exact match if multiple words
        if search_terms:
            if isinstance(search_terms, list):
                terms = []
                for term in search_terms:
                    if " " in term:  # If term contains spaces, use quotes
                        terms.append(f'"{term}"')
                    else:
                        terms.append(term)
                terms_str = " OR ".join(terms)
                query_parts.append(f"({terms_str})")
            else:
                if " " in search_terms:  # If term contains spaces, use quotes
                    query_parts.append(f'"{search_terms}"')
                else:
                    query_parts.append(search_terms)
        
        # Join query parts with AND
        query = " AND ".join(query_parts) if query_parts else ""
        
        print(f"Searching arXiv with query: {query}")
        
        # Create the search object
        search = arxiv.Search(
            query=query,
            max_results=100,  # Fetch more than we need to account for duplicates
            sort_by=arxiv.SortCriterion.SubmittedDate,
            sort_order=arxiv.SortOrder.Descending  # Most recent first
        )
        
        # Fetch results
        results_generator = self.client.results(search)
        
        # Track papers we've found in this search session
        found_papers = []
        seen_in_this_run = set()
        
        # Get up to max_results papers we haven't seen before
        for paper in results_generator:
            paper_id = paper.entry_id.split('/')[-1]
            
            # Skip if we've already seen this paper before
            if paper_id in self.seen_papers or paper_id in seen_in_this_run:
                print(f"Skipping already seen paper: {paper.title}")
                continue
            
            # Convert the paper to our format and add it to the results
            paper_dict = self._convert_result(paper)
            found_papers.append(paper_dict)
            seen_in_this_run.add(paper_id)
            
            # Check if we have enough papers
            if len(found_papers) >= max_results:
                break
        
        # Mark all new papers as seen
        self.mark_papers_as_seen(found_papers)
        
        return found_papers
    
    def get_paper_by_id(self, paper_id):
        """
        Retrieve a specific paper by its arXiv ID.
        
        Args:
            paper_id: The arXiv ID of the paper
            
        Returns:
            dict: A dictionary containing the paper's metadata
        """
        search = arxiv.Search(id_list=[paper_id])
        try:
            result = next(self.client.results(search))
            return self._convert_result(result)
        except StopIteration:
            return None
    
    def get_pdf_url(self, paper_id):
        """
        Get the PDF URL for a paper.
        
        Args:
            paper_id: The arXiv ID of the paper
            
        Returns:
            str: The URL to the PDF
        """
        paper = self.get_paper_by_id(paper_id)
        if paper and paper.pdf_url:
            return paper.pdf_url
        
        raise ValueError(f"Paper with ID {paper_id} not found or has no PDF URL.")
    
    def _convert_result(self, result):
        """
        Convert an arxiv.Result object to a standardized dictionary.
        
        Args:
            result: An arxiv.Result object
            
        Returns:
            dict: A dictionary containing paper metadata
        """
        # Extract the arXiv ID from the entry ID URL
        arxiv_id = result.entry_id.split('/')[-1]
        
        # Get PDF URL and ensure it uses HTTPS
        pdf_url = result.pdf_url if hasattr(result, 'pdf_url') else f"https://arxiv.org/pdf/{arxiv_id}.pdf"
        if pdf_url.startswith('http:'):
            pdf_url = 'https' + pdf_url[4:]

        paper = PaperData(
            id=arxiv_id,
            categories=result.categories,
            title=result.title,
            url=result.entry_id,
            published=result.published.isoformat() if hasattr(result, 'published') else None,
            authors=[author.name for author in result.authors],
            abstract=result.summary,
            keywords=result.categories,
            pdf_url=pdf_url
        )
        
        # Add DOI if available
        if hasattr(result, 'doi'):
            paper.doi = result.doi
        
        # Add comment if available
        if hasattr(result, 'comment'):
            paper.comment = result.comment
            
        return paper