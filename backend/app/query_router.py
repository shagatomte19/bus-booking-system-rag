import os
from openai import OpenAI
from sqlalchemy.orm import Session
from sqlalchemy import func  
from .models import BusProvider, District, DroppingPoint, provider_coverage
from .rag_pipeline import get_rag_pipeline
import logging
import json

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class QueryRouter:
    def __init__(self):
        self.llm_api_key = os.getenv("llm_API_KEY")
        if not self.llm_api_key:
            logger.warning("llm_API_KEY not set.")
        else:
            self.client = OpenAI(api_key=self.llm_api_key, base_url="https://openrouter.ai/api/v1")
        
        self.rag_pipeline = get_rag_pipeline()
    
    def classify_query(self, question: str) -> str:
        """
        Classify the query type using keyword matching
        Returns: 'route_search', 'provider_info', or 'general'
        """
        question_lower = question.lower()
        
        # Route search keywords
        route_keywords = [
            'from', 'to', 'route', 'price', 'taka', 'fare', 'cost',
            'bus', 'buses', 'operate', 'operating', 'providers',
            'availability', 'schedule', 'available', 'go', 'goes',
            'cheapest', 'expensive', 'show all', 'list', 'which buses',
            'travel', 'journey', 'trip'
        ]
        
        # Provider info keywords
        provider_keywords = [
            'contact', 'address', 'phone', 'email', 'call', 'number',
            'privacy', 'policy', 'policies', 'details', 'information',
            'about', 'tell me about', 'company', 'office', 'location',
            'refund', 'cancellation', 'baggage', 'discount'
        ]
        
        # Check for route search
        route_score = sum(1 for keyword in route_keywords if keyword in question_lower)
        provider_score = sum(1 for keyword in provider_keywords if keyword in question_lower)
        
        logger.info(f"Classification scores - route: {route_score}, provider: {provider_score}")
        
        if route_score > provider_score:
            return 'route_search'
        elif provider_score > 0:
            return 'provider_info'
        else:
            return 'general'
    
    def search_routes(self, question: str, db: Session) -> dict:
        """
        Extract search parameters from natural language and query database
        """
        prompt = f"""Extract bus search parameters from this question. Return a JSON object with these fields:
- from_district: origin district name (or null if not specified)
- to_district: destination district name (or null if not specified)  
- max_price: maximum price in taka (or null if not specified)

Available districts: Dhaka, Chattogram, Khulna, Rajshahi, Sylhet, Barishal, Rangpur, Mymensingh, Comilla, Bogra

Question: {question}

Return ONLY valid JSON, no explanation. Example: {{"from_district": "Dhaka", "to_district": "Rajshahi", "max_price": 500}}"""
        
        try:
            response1 = self.client.chat.completions.create(
                model="openai/gpt-oss-20b:free",
                messages=[{"role": "user", "content": prompt}],
                max_tokens=200
            )
            
            response_text = response1.choices[0].message.content.strip()
            logger.info(f"Parameter extraction response: {response_text}")
            
            # Remove markdown code blocks if present
            if response_text.startswith('```'):
                lines = response_text.split('\n')
                response_text = '\n'.join(lines[1:-1]) if len(lines) > 2 else response_text
                if response_text.startswith('json'):
                    response_text = response_text[4:].strip()
            
            params = json.loads(response_text.strip())
            logger.info(f"Extracted parameters: {params}")
            
            from_district = params.get('from_district')
            to_district = params.get('to_district')
            max_price = params.get('max_price')
            
            # Query database
            results = []
            
            if from_district and to_district:
                # Find districts
                from_dist = db.query(District).filter(District.name == from_district).first()
                to_dist = db.query(District).filter(District.name == to_district).first()
                
                logger.info(f"Found districts - From: {from_dist}, To: {to_dist}")
                
                if from_dist and to_dist:
                    # Find providers covering both districts - FIXED: using func directly
                    providers = db.query(BusProvider).join(
                        provider_coverage, BusProvider.id == provider_coverage.c.provider_id
                    ).filter(
                        provider_coverage.c.district_id.in_([from_dist.id, to_dist.id])
                    ).group_by(BusProvider.id).having(
                        func.count(provider_coverage.c.district_id) == 2  # ← FIXED
                    ).all()
                    
                    logger.info(f"Found {len(providers)} providers covering both districts")
                    
                    # Get dropping points
                    dropping_points_query = db.query(DroppingPoint).filter(
                        DroppingPoint.district_id == to_dist.id
                    )
                    
                    if max_price:
                        dropping_points_query = dropping_points_query.filter(DroppingPoint.price <= max_price)
                    
                    dropping_points = dropping_points_query.all()
                    logger.info(f"Found {len(dropping_points)} dropping points")
                    
                    for provider in providers:
                        for dp in dropping_points:
                            results.append({
                                'provider': provider.name,
                                'from': from_district,
                                'to': to_district,
                                'drop_point': dp.name,
                                'price': dp.price
                            })
                    
                    logger.info(f"Total results: {len(results)}")
                else:
                    logger.warning(f"Districts not found - from_dist: {from_dist}, to_dist: {to_dist}")
            else:
                logger.warning(f"Missing parameters - from: {from_district}, to: {to_district}")
            
            return {
                'found': len(results) > 0,
                'results': results,
                'params': params
            }
            
        except json.JSONDecodeError as e:
            logger.error(f"JSON decode error: {e}, Response was: {response_text}")
            return {'found': False, 'results': [], 'params': {}, 'error': 'Failed to parse parameters'}
        except Exception as e:
            logger.error(f"Error searching routes: {e}", exc_info=True)
            return {'found': False, 'results': [], 'params': {}, 'error': str(e)}
    
    def generate_natural_response(self, question: str, data: dict, query_type: str) -> str:
        """
        Generate natural language response
        """
        # FIXED: Check for errors first
        if 'error' in data:
            return f"I encountered an error while searching: {data['error']}. Please try rephrasing your question."
        
        if not self.llm_api_key:
            if query_type == 'route_search' and data.get('found'):
                results = data['results']
                response = f"Found {len(results)} bus(es):\n"
                for r in results:
                    response += f"- {r['provider']}: {r['from']} → {r['to']} at {r['drop_point']} for ৳{r['price']}\n"
                return response
            elif query_type == 'route_search':
                return "No buses found matching your criteria. Please try different districts or a higher price limit."
            else:
                return "API key not configured."
        
        if query_type == 'route_search':
            if data.get('found'):
                # FIXED: Use ACTUAL data from database
                results = data['results']
                results_text = "\n".join([
                    f"- {r['provider']}: {r['from']} to {r['to']} (Drop: {r['drop_point']}, Price: ৳{r['price']})"
                    for r in results
                ])
                
                prompt = f"""The user asked: "{question}"

Database query results (REAL DATA):
{results_text}

Provide a helpful response using ONLY the information above. List the buses with their exact prices and drop points. Do not make up any information."""
            else:
                params = data.get('params', {})
                prompt = f"""The user asked: "{question}"

Search parameters: {params}

NO buses were found in the database matching these criteria. Explain this clearly and suggest trying:
- Different districts
- Higher price limit
- Checking if the route exists"""
        
        elif query_type == 'provider_info':
            prompt = f"""The user asked: "{question}"

Information found:
{data.get('answer', 'No information found.')}

Sources: {', '.join(data.get('sources', []))}

Provide a helpful response based ONLY on the information above."""
        
        else:
            prompt = f"""The user asked: "{question}"

Provide a brief, helpful response about the bus booking system. Keep it short and friendly."""
        
        try:
            response3 = self.client.chat.completions.create(
                model="openai/gpt-oss-20b:free",
                messages=[{"role": "user", "content": prompt}],
                max_tokens=500
            )
            return response3.choices[0].message.content
        except Exception as e:
            logger.error(f"Error generating response: {e}")
            return "Sorry, I encountered an error generating a response."
    
    def answer_question(self, question: str, db: Session) -> dict:
        """
        Main method to answer any question
        """
        # Classify the query
        query_type = self.classify_query(question)
        logger.info(f"Query classified as: {query_type}")
        
        if query_type == 'route_search':
            # Search database for routes
            search_data = self.search_routes(question, db)
            logger.info(f"Search results: found={search_data.get('found')}, count={len(search_data.get('results', []))}")
            
            answer = self.generate_natural_response(question, search_data, query_type)
            
            return {
                'answer': answer,
                'type': 'route_search',
                'data': search_data['results'] if search_data.get('found') else []
            }
        
        elif query_type == 'provider_info':
            # Use RAG for provider information
            rag_result = self.rag_pipeline.ask(question)
            answer = self.generate_natural_response(question, rag_result, query_type)
            
            return {
                'answer': answer,
                'type': 'provider_info',
                'sources': rag_result.get('sources', [])
            }
        
        else:
            # General question
            answer = self.generate_natural_response(question, {}, query_type)
            return {
                'answer': answer,
                'type': 'general'
            }


# Global instance
query_router = None


def get_query_router() -> QueryRouter:
    """Get or create QueryRouter instance"""
    global query_router
    if query_router is None:
        query_router = QueryRouter()
    return query_router