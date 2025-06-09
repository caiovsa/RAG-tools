import sys
import os

# Adiciona caminhos necessários
sys.path.append(os.path.join(os.path.dirname(__file__), '..'))
sys.path.append(os.path.join(os.path.dirname(__file__), '..', 'rag-core'))

from data_connectors.web_search_tool import WebSearchTool, search_web_and_get_context

def test_web_search():
    """Testa a ferramenta de web search"""
    print("🚀 Testando Web Search Tool")
    print("=" * 50)
    
    # Teste básico
    tool = WebSearchTool(max_results=3)
    
    query = "Como printar no python?"
    print(f"🔍 Query: {query}")
    
    # Busca e scraping
    results = tool.search_and_scrape(query)
    
    if results:
        print(f"\n📊 Resultados encontrados: {len(results)}")
        
        for i, result in enumerate(results, 1):
            print(f"\n{i}. {result['title']}")
            print(f"   URL: {result['url']}")
            print(f"   Content preview: {result['content'][:200]}...")
        
        # Prepara para RAG
        rag_docs = tool.prepare_for_rag(results)
        print(f"\n📝 Documentos preparados para RAG: {len(rag_docs)}")
        
        # Mostra exemplo de documento RAG
        if rag_docs:
            print(f"\n📄 Exemplo de documento RAG:")
            print(f"   Text: {rag_docs[0]['text'][:200]}...")
            print(f"   Source: {rag_docs[0]['source_url']}")
    
    else:
        print("❌ Nenhum resultado encontrado")

if __name__ == "__main__":
    test_web_search()
