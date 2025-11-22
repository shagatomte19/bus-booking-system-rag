import os
import chromadb
from chromadb.config import Settings
from openai import OpenAI
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class RAGPipeline:
    def __init__(self):
        # Initialize ChromaDB client
        chroma_host = os.getenv("CHROMA_HOST", "localhost")
        chroma_port = int(os.getenv("CHROMA_PORT", "8000"))
        
        self.chroma_client = chromadb.HttpClient(
            host=chroma_host,
            port=chroma_port,
            settings=Settings(anonymized_telemetry=False)
        )
        
        # Get or create collection
        try:
            self.collection = self.chroma_client.get_or_create_collection(
                name="bus_providers",
                metadata={"description": "Bus provider information and policies"}
            )
            logger.info("ChromaDB collection initialized successfully")
        except Exception as e:
            logger.error(f"Error initializing ChromaDB: {e}")
            raise
        
        # Initialize OpenRouter client
        self.api_key = os.getenv("xAI_API_KEY")
        if not self.api_key:
            logger.warning("xAI_API_KEY not set. RAG queries will fail.")
        else:
            self.client = OpenAI(api_key=self.api_key, base_url="https://openrouter.ai/api/v1")
            logger.info(f"OpenRouter client initialized with key: {self.api_key[:10]}...")
    
    def index_documents(self, provider_files_dir: str):
        """
        Index all provider documents into ChromaDB
        """
        import glob
        
        provider_files = glob.glob(os.path.join(provider_files_dir, "*.txt"))
        
        if not provider_files:
            logger.warning(f"No provider files found in {provider_files_dir}")
            return
        
        # Check if collection already has documents
        existing_count = self.collection.count()
        if existing_count > 0:
            logger.info(f"Collection already has {existing_count} documents. Skipping indexing.")
            return
        
        documents = []
        metadatas = []
        ids = []
        
        for idx, file_path in enumerate(provider_files):
            try:
                with open(file_path, 'r', encoding='utf-8') as f:
                    content = f.read()
                
                # Extract provider name from filename
                provider_name = os.path.basename(file_path).replace('.txt', '').replace('_', ' ').title()
                
                # STRATEGY 1: Always index the COMPLETE document (most important)
                documents.append(content)
                metadatas.append({
                    "provider": provider_name,
                    "source_file": os.path.basename(file_path),
                    "chunk_type": "complete"
                })
                ids.append(f"{provider_name}_complete")
                
                # STRATEGY 2: Extract and index KEY SECTIONS separately
                # Look for common patterns in provider files
                lines = content.split('\n')
                
                # Find and index contact section
                contact_section = []
                address_section = []
                policy_section = []
                
                for i, line in enumerate(lines):
                    line_lower = line.lower()
                    
                    # Capture contact information (with context)
                    if 'contact' in line_lower or 'phone' in line_lower or 'email' in line_lower or 'tel:' in line_lower:
                        # Get this line and next 2 lines for complete context
                        contact_section.extend(lines[max(0, i-1):min(len(lines), i+3)])
                    
                    # Capture address
                    if 'address' in line_lower or 'official address' in line_lower:
                        address_section.extend(lines[max(0, i-1):min(len(lines), i+3)])
                    
                    # Capture privacy policy section
                    if 'privacy' in line_lower:
                        policy_section.extend(lines[max(0, i-1):min(len(lines), i+5)])
                
                # Index contact section if found
                if contact_section:
                    contact_text = '\n'.join(set(contact_section))  # Remove duplicates
                    documents.append(contact_text)
                    metadatas.append({
                        "provider": provider_name,
                        "source_file": os.path.basename(file_path),
                        "chunk_type": "contact"
                    })
                    ids.append(f"{provider_name}_contact")
                
                # Index address section if found
                if address_section:
                    address_text = '\n'.join(set(address_section))
                    documents.append(address_text)
                    metadatas.append({
                        "provider": provider_name,
                        "source_file": os.path.basename(file_path),
                        "chunk_type": "address"
                    })
                    ids.append(f"{provider_name}_address")
                
                logger.info(f"Indexed {provider_name}: 1 complete + {len(contact_section) > 0} contact + {len(address_section) > 0} address chunks")
            
            except Exception as e:
                logger.error(f"Error reading {file_path}: {e}")
                continue
        
        if documents:
            try:
                # Add documents to ChromaDB
                self.collection.add(
                    documents=documents,
                    metadatas=metadatas,
                    ids=ids
                )
                logger.info(f"Successfully indexed {len(documents)} document chunks")
            except Exception as e:
                logger.error(f"Error adding documents to ChromaDB: {e}")
    
    def retrieve_relevant_context(self, query: str, n_results: int = 5) -> tuple:
        """
        Retrieve relevant document chunks for a query
        IMPROVED: Smart retrieval that prioritizes complete documents for specific queries
        """
        try:
            # First, try to get more results
            results = self.collection.query(
                query_texts=[query],
                n_results=min(n_results + 3, 10)  # Get extra results
            )
            
            documents = results['documents'][0] if results['documents'] else []
            metadatas = results['metadatas'][0] if results['metadatas'] else []
            
            # Smart filtering: If query mentions a specific provider, prioritize that provider's complete doc
            query_lower = query.lower()
            
            # Detect if query is about a specific provider
            providers_mentioned = []
            for meta in metadatas:
                provider = meta.get('provider', '')
                if provider.lower() in query_lower:
                    providers_mentioned.append(provider)
            
            # Re-order results: put complete documents of mentioned providers first
            final_docs = []
            final_metas = []
            
            # First: Add complete documents of mentioned providers
            for doc, meta in zip(documents, metadatas):
                if (meta.get('chunk_type') == 'complete' and 
                    meta.get('provider') in providers_mentioned):
                    final_docs.append(doc)
                    final_metas.append(meta)
            
            # Second: Add contact/address specific chunks
            for doc, meta in zip(documents, metadatas):
                if meta.get('chunk_type') in ['contact', 'address']:
                    if doc not in final_docs:  # Avoid duplicates
                        final_docs.append(doc)
                        final_metas.append(meta)
            
            # Third: Add other relevant chunks
            for doc, meta in zip(documents, metadatas):
                if doc not in final_docs and len(final_docs) < n_results:
                    final_docs.append(doc)
                    final_metas.append(meta)
            
            # Limit to n_results
            final_docs = final_docs[:n_results]
            final_metas = final_metas[:n_results]
            
            logger.info(f"Retrieved {len(final_docs)} chunks for query: {query}")
            for i, (doc, meta) in enumerate(zip(final_docs, final_metas)):
                logger.info(f"  Chunk {i+1}: {meta.get('provider')} ({meta.get('chunk_type')}) - {doc[:100]}...")
            
            return final_docs, final_metas
        
        except Exception as e:
            logger.error(f"Error retrieving context: {e}")
            return [], []
    
    def generate_answer(self, query: str, context_docs: list, context_metadata: list) -> str:
        """
        Generate an answer using OpenRouter with retrieved context
        """
        if not self.api_key:
            return "Error: xAI API key not configured. Please set xAI_API_KEY environment variable."
        
        if not context_docs:
            return "I couldn't find any relevant information about that in the bus provider documents."
        
        # Prepare context string with clear separation
        context_str = "\n\n=== DOCUMENT START ===\n\n".join([
            f"Provider: {meta['provider']}\nContent:\n{doc}"
            for doc, meta in zip(context_docs, context_metadata)
        ])
        
        # Create prompt for LLM
        prompt = f"""You are a helpful assistant for a bus ticket booking system. Answer the user's question based ONLY on the information provided below.

IMPORTANT: 
- Use ALL the information from the documents below
- Format your response in a clean, readable way
- If contact details exist, format them with emojis: 📍 for address, 📞 for phone, 📧 for email, 🌐 for website
- Use bullet points or numbered lists for clarity
- Do not say information is missing if it's in the documents
- Keep the response concise but complete

=== DOCUMENTS ===
{context_str}

=== USER QUESTION ===
{query}

Provide a well-formatted answer using ALL relevant information from the documents above."""
        
        try:
            response = self.client.chat.completions.create(
                model="openai/gpt-4o-mini",
                messages=[{"role": "user", "content": prompt}],
                max_tokens=1000,
                temperature=0.3  # Lower for more factual responses
            )
            
            return response.choices[0].message.content
        
        except Exception as e:
            logger.error(f"Error generating answer with OpenRouter: {e}")
            return f"Error generating response: {str(e)}"
    
    def ask(self, question: str) -> dict:
        """
        Main method to ask a question using RAG pipeline
        """
        # Retrieve relevant context (more chunks for complete info)
        context_docs, context_metadata = self.retrieve_relevant_context(question, n_results=5)
        
        # Generate answer
        answer = self.generate_answer(question, context_docs, context_metadata)
        
        # Extract source providers
        sources = list(set([meta['provider'] for meta in context_metadata]))
        
        return {
            "answer": answer,
            "sources": sources
        }


# Global RAG pipeline instance
rag_pipeline = None


def get_rag_pipeline() -> RAGPipeline:
    """
    Get or create RAG pipeline instance
    """
    global rag_pipeline
    if rag_pipeline is None:
        rag_pipeline = RAGPipeline()
    return rag_pipeline