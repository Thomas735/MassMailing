import logging
from googlesearch import search
import time

class ScraperManager:
    def __init__(self):
        self.logger = logging.getLogger(__name__)

    def search_gigs(self, city, additional_keywords="", num_results=20):
        """
        Scrapes Google for gig opportunities based on city and keywords.
        """
        self.logger.info(f"Démarrage du scraping pour la ville: {city}")
        
        # Build the exact query
        # Using OR operators to find "cherche groupe", "recherche groupe", or "appel à candidature" 
        # specifically in combination with the city name and "concert".
        query_parts = []
        if additional_keywords:
            query_parts.append(additional_keywords)
        else:
            query_parts.append('("cherche groupe" OR "recherche groupe" OR "appel à artistes" OR "programmation musicale" OR "appel a projet")')
            
        query_parts.append('concert')
        if city:
            query_parts.append(city)
            
        query = " ".join(query_parts)
        self.logger.info(f"Requête Google: {query}")
        
        results = []
        try:
            # We use the advanced option to get title, url, description
            # pause=2 to avoid rate limiting blocks by Google (HTTP 429)
            for result in search(query, num=num_results, stop=num_results, pause=2.0, advanced=True):
                # googlesearch_python returns SearchResult objects when advanced=True
                # possessing .title, .url, .description attributes
                results.append({
                    "title": result.title,
                    "url": result.url,
                    "description": result.description
                })
        except Exception as e:
            self.logger.error(f"Erreur lors du scraping Google : {e}")
            
        return results
