import sys
import os
import re
from typing import Optional, Dict
from deep_translator import GoogleTranslator
from langdetect import detect  # Mantém só a função detect

# Adiciona o rag-core ao path
sys.path.append(os.path.join(os.path.dirname(__file__), '..', 'rag-core'))

class TradutorTool:
    """Ferramenta de tradução integrada ao RAG"""
    
    def __init__(self):
        # Com deep-translator não precisamos instanciar aqui
        # Criamos o tradutor conforme necessário
        
        # Mapeamento de idiomas comuns
        self.idiomas = {
            'pt': 'português',
            'en': 'inglês', 
            'es': 'espanhol',
            'fr': 'francês',
            'de': 'alemão',
            'it': 'italiano',
            'ja': 'japonês',
            'ko': 'coreano',
            'zh': 'chinês',
            'ru': 'russo'
        }
    
    def detectar_idioma(self, texto: str) -> Dict[str, str]:
        """Detecta o idioma do texto"""
        try:
            # Usa langdetect diretamente
            idioma_codigo = detect(texto)
            idioma_nome = self.idiomas.get(idioma_codigo, idioma_codigo)
            
            return {
                'codigo': idioma_codigo,
                'nome': idioma_nome,
                'confianca': 'alta'
            }
        except Exception as e:
            print(f"❌ Erro na detecção: {e}")
            return {
                'codigo': 'pt',  # Fallback para português
                'nome': 'português',
                'confianca': 'baixa'
            }
    
    def extrair_texto_para_traduzir(self, query: str) -> Optional[str]:
        """Extrai o texto a ser traduzido da query"""
        # Versão simplificada - mais robusta
        if query.lower().startswith('traduz:'):
            texto = query[7:].strip()
        elif query.lower().startswith('traduz '):
            texto = query[7:].strip()
        elif query.lower().startswith('translate:'):
            texto = query[10:].strip()
        elif query.lower().startswith('translate '):
            texto = query[10:].strip()
        else:
            return None
        
        # Remove aspas se houver
        texto = texto.strip('"\'')
        return texto if texto else None
    
    def traduzir_automatico(self, texto: str) -> Dict[str, str]:
        """Traduz automaticamente baseado no idioma detectado"""
        try:
            print(f"🔍 Detectando idioma de: {texto[:50]}...")
            
            # Detecta idioma
            deteccao = self.detectar_idioma(texto)
            idioma_origem = deteccao['codigo']
            
            print(f"🗣️ Idioma detectado: {deteccao['nome']}")
            
            # Define idioma destino
            if idioma_origem == 'pt':
                idioma_destino = 'en'
                nome_destino = 'inglês'
            else:
                idioma_destino = 'pt'
                nome_destino = 'português'
            
            print(f"🎯 Traduzindo para: {nome_destino}")
            
            # AQUI É A MUDANÇA PRINCIPAL - sintaxe do deep-translator
            tradutor = GoogleTranslator(source=idioma_origem, target=idioma_destino)
            traducao = tradutor.translate(texto)
            
            return {
                'texto_original': texto,
                'idioma_origem': deteccao['nome'],
                'idioma_destino': nome_destino,
                'traducao': traducao,  # deep-translator retorna string diretamente
                'sucesso': True
            }
            
        except Exception as e:
            print(f"❌ Erro na tradução: {e}")
            return {
                'texto_original': texto,
                'erro': str(e),
                'sucesso': False
            }
    
    def traduzir_para_idioma(self, texto: str, idioma_destino: str) -> Dict[str, str]:
        """Traduz para um idioma específico"""
        try:
            # Converte nome do idioma para código se necessário
            codigo_destino = idioma_destino.lower()
            
            # Mapeamento de nomes para códigos
            nomes_para_codigos = {v: k for k, v in self.idiomas.items()}
            if codigo_destino in nomes_para_codigos:
                codigo_destino = nomes_para_codigos[codigo_destino]
            
            # Detecta idioma origem
            deteccao = self.detectar_idioma(texto)
            idioma_origem = deteccao['codigo']
            
            print(f"🎯 Traduzindo de {deteccao['nome']} para {self.idiomas.get(codigo_destino, codigo_destino)}")
            
            # MUDANÇA: sintaxe do deep-translator
            tradutor = GoogleTranslator(source=idioma_origem, target=codigo_destino)
            traducao = tradutor.translate(texto)
            
            return {
                'texto_original': texto,
                'idioma_origem': deteccao['nome'],
                'idioma_destino': self.idiomas.get(codigo_destino, codigo_destino),
                'traducao': traducao,  # String direta
                'sucesso': True
            }
            
        except Exception as e:
            print(f"❌ Erro na tradução específica: {e}")
            return {
                'texto_original': texto,
                'erro': str(e),
                'sucesso': False
            }
    
    def processar_comando_traducao(self, query: str) -> str:
        """Processa comando de tradução completo"""
        print(f"📝 Query recebida: {query}")
        
        # Extrai texto para traduzir
        texto = self.extrair_texto_para_traduzir(query)
        
        if not texto:
            return """❌ Não consegui identificar o texto para traduzir.

💡 **Como usar:**
• `traduz: Olá, como você está?`
• `traduz: Hello, how are you?`
• `traduz para inglês: Bom dia`
• `traduz para espanhol: Good morning`

📝 **Idiomas suportados:** português, inglês, espanhol, francês, alemão, italiano, japonês, coreano, chinês, russo"""

        print(f"📝 Texto extraído: {texto}")

        # Verifica se é tradução para idioma específico
        if "para " in query.lower():
            # Extrai idioma destino
            match = re.search(r'para\s+(\w+)', query.lower())
            if match:
                idioma_destino = match.group(1)
                print(f"🎯 Tradução específica para: {idioma_destino}")
                resultado = self.traduzir_para_idioma(texto, idioma_destino)
            else:
                resultado = self.traduzir_automatico(texto)
        else:
            # Tradução automática
            resultado = self.traduzir_automatico(texto)
        
        # Formata resposta
        if resultado['sucesso']:
            resposta = f"""🌐 **Tradução realizada:**

📝 **Texto original:** {resultado['texto_original']}
🗣️ **Idioma origem:** {resultado['idioma_origem']}
🎯 **Idioma destino:** {resultado['idioma_destino']}

✅ **Tradução:** {resultado['traducao']}"""
        else:
            resposta = f"❌ **Erro na tradução:** {resultado.get('erro', 'Erro desconhecido')}"
        
        return resposta

# Função de detecção para usar no chat
def detectar_comando_traducao(query: str) -> bool:
    """Detecta se a query é um comando de tradução"""
    comandos = ['traduz:', 'traduz ', 'translate:', 'translate ']
    query_lower = query.lower().strip()
    
    return any(query_lower.startswith(cmd) for cmd in comandos)

# Função utilitária para usar no chat
def processar_traducao(query: str) -> str:
    """Função simples para usar a ferramenta de tradução"""
    print(f"🌍 Iniciando processamento: {query}")
    tool = TradutorTool()
    return tool.processar_comando_traducao(query)
