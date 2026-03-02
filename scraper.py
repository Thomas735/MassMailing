import logging
import requests
from bs4 import BeautifulSoup

class ScraperManager:
    def __init__(self):
        self.logger = logging.getLogger(__name__)

    def search_gigs(self, city, additional_keywords="", num_results=15):
        """
        Scrapes Google for gig opportunities based on city and keywords.
        """
        self.logger.info(f"Démarrage du scraping pour la ville: {city}")
        
        query_parts = []
        if additional_keywords:
            query_parts.append(additional_keywords)
        else:
            query_parts.append('("cherche groupe" OR "recherche groupe" OR "appel à artistes" OR "programmation musicale")')
            
        query_parts.append('concert')
        if city:
            query_parts.append(city)
            
        query = " ".join(query_parts)
        self.logger.info(f"Requête Google: {query}")
        
        results = []
        try:
            headers = {
                "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
                "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8"
            }
            # DuckDuckGo HTML version is much more lenient for basic scraping than Google
            url = f"https://html.duckduckgo.com/html/?q={requests.utils.quote(query)}"
            response = requests.get(url, headers=headers, timeout=10)
            response.raise_for_status()

            soup = BeautifulSoup(response.text, "html.parser")
            
            for result_block in soup.find_all('div', class_='result'):
                
                title_a = result_block.find('a', class_='result__url')
                if title_a:
                    link = title_a.get('href')
                    
                    # DuckDuckGo wraps links in a tiny redirect sometimes, we can try to clean it
                    if link and 'uddg=' in link:
                        import urllib.parse
                        parsed = urllib.parse.urlparse(link)
                        params = urllib.parse.parse_qs(parsed.query)
                        if 'uddg' in params:
                            link = params['uddg'][0]

                    title_h2 = result_block.find('h2', class_='result__title')
                    title_text = title_h2.get_text(strip=True) if title_h2 else "Titre non disponible"
                    
                    snippet_a = result_block.find('a', class_='result__snippet')
                    snippet_text = snippet_a.get_text(strip=True) if snippet_a else "Description non disponible."
                    
                    results.append({
                        "title": title_text,
                        "url": link,
                        "description": snippet_text
                    })
                    
                    if len(results) >= num_results:
                        break
                            
        except Exception as e:
            self.logger.error(f"Erreur lors du scraping : {e}")
            
        return results
