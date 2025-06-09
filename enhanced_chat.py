import sys
import os
from typing import List, Dict

# Adiciona paths
sys.path.append(os.path.join(os.path.dirname(__file__), 'rag-core'))
sys.path.append(os.path.dirname(__file__))

# Imports do rag-core
from config import settings
from chat import (
    initialize_connections, generate_query_embedding, 
    search_similar_documents, collection
)

# Import da nova ferramenta
from data_connectors.web_search_tool import WebSearchTool
from data_connectors.tradutor_tool import detectar_comando_traducao, processar_traducao


# Global variables
web_search_tool = None

def setup_enhanced_chat():
    """Inicializa chat com web search"""
    global web_search_tool
    
    # Inicializa conexões normais do RAG
    if not initialize_connections():
        return False
    
    # Inicializa web search tool
    web_search_tool = WebSearchTool(max_results=3)
    print("🌐 Web Search Tool inicializada")
    
    return True

def enhanced_search(query: str, use_web_search: bool = False) -> List[Dict]:
    """Busca aprimorada que pode usar web search"""
    all_docs = []
    
    # 1. Busca no RAG local (sempre)
    local_docs = search_similar_documents(query, top_k=3)
    if local_docs:
        # Adiciona source type
        for doc in local_docs:
            doc['source_type'] = 'local_rag'
        all_docs.extend(local_docs)
        print(f"📚 Encontrados {len(local_docs)} documentos locais")
    
    # 2. Busca na web (se habilitado)
    if use_web_search:
        print("🌐 Fazendo busca na web...")
        web_results = web_search_tool.search_and_scrape(query)
        
        if web_results:
            # Converte para formato similar ao RAG local
            for result in web_results:
                all_docs.append({
                    'text': result['content'][:1000],  # Limita tamanho
                    'file_name': result['title'],
                    'page_number': 1,
                    'score': 0.8,  # Score fixo para web results
                    'source_type': 'web_search',
                    'source_url': result['url']
                })
            print(f"🌐 Encontrados {len(web_results)} resultados web")
    
    return all_docs

def generate_enhanced_response(query: str, context_docs: List[Dict]) -> str:
    """Gera resposta usando contexto local + web"""
    # Separa contextos por tipo
    local_context = []
    web_context = []
    
    for doc in context_docs:
        if doc.get('source_type') == 'web_search':
            web_context.append(doc)
        else:
            local_context.append(doc)
    
    # Monta contexto combinado
    context_parts = []
    
    if local_context:
        local_text = "\n\n".join([
            f"Do documento local {doc['file_name']} (página {doc['page_number']}):\n{doc['text']}"
            for doc in local_context
        ])
        context_parts.append(f"CONTEXTO DOS DOCUMENTOS LOCAIS:\n{local_text}")
    
    if web_context:
        web_text = "\n\n".join([
            f"Do site {doc['file_name']} ({doc.get('source_url', 'N/A')}):\n{doc['text']}"
            for doc in web_context
        ])
        context_parts.append(f"CONTEXTO DA BUSCA WEB:\n{web_text}")
    
    combined_context = "\n\n" + "="*50 + "\n\n".join(context_parts)
    
    # Importa função de geração do rag-core
    from chat import generate_response
    
    # Usa a função existente com contexto aprimorado
    fake_docs = [{'file_name': 'combined', 'page_number': 1, 'text': combined_context}]
    return generate_response(query, fake_docs)

def enhanced_chat_loop():
    """Loop principal do chat aprimorado"""
    print("\n🤖 Enhanced RAG Chat Assistant")
    print("=" * 60)
    print("Comandos disponíveis:")
    print("📚 Busca normal: 'Qual é a capital do Brasil?'")
    print("🌐 Busca web: 'web: últimas notícias sobre IA'")
    print("🌍 Tradução: 'traduz: Hello, how are you?'")
    print("🌍 Tradução específica: 'traduz para inglês: Bom dia'")
    print("❌ Sair: 'quit'")
    print()
    
    while True:
        try:
            query = input("Você: ").strip()
            
            if query.lower() in ['quit', 'exit', 'bye', 'sair']:
                print("👋 Até logo!")
                break
            
            if not query:
                continue
            
            # 1. Verifica se é comando de tradução
            if detectar_comando_traducao(query):
                print("🌍 Processando tradução...")
                response = processar_traducao(query)
                print(f"\nAssistente: {response}\n")
                continue
            
            # 2. Verifica se deve usar web search
            use_web = query.lower().startswith('web:')
            if use_web:
                query = query[4:].strip()
                print("🌐 Modo web search ativado")
            
            print("🔍 Buscando informações...")
            
            # 3. Busca aprimorada (local + web se necessário)
            docs = enhanced_search(query, use_web_search=use_web)
            
            if not docs:
                print("❌ Nenhuma informação relevante encontrada.")
                continue
            
            print(f"📊 Encontradas {len(docs)} fontes de informação")
            
            # 4. Gera resposta
            print("🤖 Gerando resposta...")
            response = generate_enhanced_response(query, docs)
            
            print(f"\nAssistente: {response}\n")
            
            # 5. Mostra fontes
            print("📖 Fontes consultadas:")
            for i, doc in enumerate(docs, 1):
                source_type = "📚 Local" if doc.get('source_type') == 'local_rag' else "🌐 Web"
                if doc.get('source_url'):
                    print(f"  {i}. {source_type}: {doc['file_name']} - {doc['source_url']}")
                else:
                    print(f"  {i}. {source_type}: {doc['file_name']} (página {doc['page_number']})")
            print()
            
        except KeyboardInterrupt:
            print("\n👋 Até logo!")
            break
        except Exception as e:
            print(f"❌ Erro: {e}")

def main():
    """Função principal"""
    if not setup_enhanced_chat():
        print("❌ Falha na inicialização")
        return
    
    enhanced_chat_loop()

if __name__ == "__main__":
    main()
