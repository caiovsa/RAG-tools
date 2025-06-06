import sys
import os
import asyncio
import requests
from typing import List, Dict, Optional
from duckduckgo_search import DDGS
from bs4 import BeautifulSoup
from urllib.parse import urljoin, urlparse
import time

# Adiciona o rag-core ao path
sys.path.append(os.path.join(os.path.dirname(__file__), '..', 'rag-core'))

# Importa do rag-core (submodule)
from config import settings
from utils import split_text, clean_text, generate_doc_id

class WebSearchTool:
    """Ferramenta para buscar informações na web e integrar ao RAG"""
    
    def __init__(self, max_results: int = 5):
        self.max_results = max_results
        self.ddgs = DDGS()
        
    def search_web(self, query: str) -> List[Dict]:
        """Faz busca na web usando DuckDuckGo"""
        try:
            print(f"🔍 Buscando na web: {query}")
            
            results = list(self.ddgs.text(
                keywords=query,
                max_results=self.max_results,
                region='pt-br',
                safesearch='moderate'
            ))
            
            print(f"📊 Encontrados {len(results)} resultados")
            return results
            
        except Exception as e:
            print(f"❌ Erro na busca: {e}")
            return []
    
    def check_robots_txt(self, url: str) -> bool:
        """Verifica se é permitido fazer scraping do site"""
        try:
            parsed_url = urlparse(url)
            robots_url = f"{parsed_url.scheme}://{parsed_url.netloc}/robots.txt"
            
            response = requests.get(robots_url, timeout=5)
            if response.status_code == 200:
                # Verificação básica - você pode melhorar isso
                robots_content = response.text.lower()
                return 'disallow: /' not in robots_content
            return True
            
        except:
            # Se não conseguir verificar, assume que é permitido
            return True
    
    def scrape_content(self, url: str) -> Optional[str]:
        """Faz scraping do conteúdo de uma URL"""
        try:
            if not self.check_robots_txt(url):
                print(f"🚫 Scraping não permitido para: {url}")
                return None
            
            print(f"📥 Fazendo scraping: {url}")
            
            headers = {
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
            }
            
            response = requests.get(url, headers=headers, timeout=10)
            response.raise_for_status()
            
            soup = BeautifulSoup(response.content, 'html.parser')
            
            # Remove scripts, styles, etc.
            for script in soup(["script", "style", "nav", "header", "footer"]):
                script.decompose()
            
            # Extrai texto limpo
            text = soup.get_text()
            text = clean_text(text)
            
            # Limita o tamanho do texto
            if len(text) > 5000:
                text = text[:5000] + "..."
            
            return text
            
        except Exception as e:
            print(f"❌ Erro no scraping de {url}: {e}")
            return None
    
    def search_and_scrape(self, query: str) -> List[Dict]:
        """Busca na web e faz scraping dos resultados"""
        # 1. Busca na web
        search_results = self.search_web(query)
        
        if not search_results:
            return []
        
        # 2. Faz scraping dos resultados
        scraped_results = []
        
        for result in search_results:
            url = result.get('href', '')
            title = result.get('title', '')
            snippet = result.get('body', '')
            
            # Tenta fazer scraping
            content = self.scrape_content(url)
            
            if content:
                scraped_results.append({
                    'url': url,
                    'title': title,
                    'snippet': snippet,
                    'content': content,
                    'source': 'web_search'
                })
            
            # Delay entre requests
            time.sleep(1)
        
        print(f"✅ Scraping concluído: {len(scraped_results)} páginas processadas")
        return scraped_results
    
    def prepare_for_rag(self, scraped_results: List[Dict]) -> List[Dict]:
        """Prepara os resultados para inserção no RAG"""
        rag_documents = []
        
        for result in scraped_results:
            # Combina título + conteúdo
            full_text = f"Título: {result['title']}\n\nConteúdo: {result['content']}"
            
            # Divide em chunks
            chunks = split_text(full_text, settings.CHUNK_SIZE, settings.CHUNK_OVERLAP)
            
            for i, chunk in enumerate(chunks):
                doc_id = f"web_{generate_doc_id(result['url'])}_{i}"
                
                rag_documents.append({
                    'text': chunk,
                    'file_name': f"web_search_{result['title'][:50]}",
                    'page_number': i + 1,
                    'chunk_id': doc_id,
                    'source_url': result['url'],
                    'source_type': 'web_search'
                })
        
        return rag_documents

# Função utilitária para usar a ferramenta
def search_web_and_get_context(query: str) -> List[Dict]:
    """Função simples para usar a web search tool"""
    tool = WebSearchTool()
    scraped_results = tool.search_and_scrape(query)
    return tool.prepare_for_rag(scraped_results)
