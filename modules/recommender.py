"""
Paper recommendation system that analyzes abstracts and recommends papers based on user interests.
"""

import logging
from typing import List, Dict, Optional
from modules.api_clients import AnthropicClient
from modules.arxiv import PaperData


class PaperRecommender:
    """
    Recommends papers based on user interests by analyzing abstracts.
    """
    
    def __init__(self, client: AnthropicClient, user_interests: str):
        """
        Initialize the paper recommender.
        
        Args:
            client: The API client for making LLM requests
            user_interests: String describing user's research interests
        """
        self._client = client
        self._user_interests = user_interests

    def _generate_recommendation_prompt(self, abstracts: List[Dict[str, str]]) -> str:
        """
        Generate a prompt for the AI model to recommend papers based on abstracts.
        
        Args:
            abstracts: List of dictionaries with 'id', 'title', and 'abstract' keys
            
        Returns:
            str: The prompt for the AI model
        """
        abstract_texts = []
        for i, paper in enumerate(abstracts, 1):
            abstract_texts.append(f"Paper {i}:\nTitle: {paper['title']}\nID: {paper['id']}\nAbstract: {paper['abstract']}\n")
        
        abstracts_section = "\n".join(abstract_texts)
        
        interests_text = self._user_interests or "general research interests"
        
        return f"""
I have {len(abstracts)} research papers and need you to recommend which ones are most relevant to my research interests. 

My research interests are: {interests_text}

Here are the papers:

{abstracts_section}

Please analyze each paper's relevance to my interests and provide recommendations. For each paper, rate its relevance on a scale of 1-5 (where 5 is highly relevant and 1 is not relevant). Only recommend papers with a relevance score of 4 or 5.

Format your response as follows:
<recommendations>
<paper id="PAPER_ID" score="RELEVANCE_SCORE" recommend="true/false">Brief explanation of why this paper is/isn't relevant to the user's interests</paper>
<!-- Repeat for each paper -->
</recommendations>

Be selective - only recommend papers that are genuinely highly relevant to the specified research interests.
"""

    def recommend_papers(self, papers: List[PaperData]) -> List[PaperData]:
        """
        Recommend papers based on their abstracts and user interests.
        
        Args:
            papers: List of PaperData objects with abstracts
            
        Returns:
            List[PaperData]: Filtered list of recommended papers
        """
        if not papers:
            return []
        
        # Prepare abstracts for analysis
        abstracts = []
        for paper in papers:
            if paper.abstract:
                abstracts.append({
                    'id': paper.id,
                    'title': paper.title,
                    'abstract': paper.abstract
                })
        
        if not abstracts:
            logging.warning("No papers with abstracts found")
            return []
        
        # Generate recommendation prompt
        prompt = self._generate_recommendation_prompt(abstracts)
        
        try:
            # Get recommendations from LLM
            response = self._client.send_request(
                prompt=prompt,
                max_tokens_to_sample=3000
            )
            
            # Parse recommendations
            recommended_ids = self._parse_recommendations(response)
            
            # Filter papers based on recommendations
            recommended_papers = [
                paper for paper in papers 
                if paper.id in recommended_ids
            ]
            
            logging.info(f"Recommended {len(recommended_papers)} out of {len(papers)} papers")
            return recommended_papers
            
        except Exception as e:
            logging.error(f"Error getting recommendations: {e}")
            # Fallback: return all papers if recommendation fails
            return papers

    def _parse_recommendations(self, response: str) -> List[str]:
        """
        Parse the LLM response to extract recommended paper IDs.
        
        Args:
            response: The LLM response containing recommendations
            
        Returns:
            List[str]: List of recommended paper IDs
        """
        import re
        
        recommended_ids = []
        
        # Extract papers marked as recommended
        pattern = r'<paper id="([^"]+)"[^>]*recommend="true"[^>]*>'
        matches = re.findall(pattern, response, re.IGNORECASE)
        
        for match in matches:
            recommended_ids.append(match)
        
        return recommended_ids