import json
import os
import sys
import time

# Add parent directory to path to allow imports
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from sqlalchemy.orm import Session
from app.database import engine, SessionLocal, Base
from app.models import District, DroppingPoint, BusProvider, provider_coverage
from app.rag_pipeline import get_rag_pipeline
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def wait_for_db(max_retries=30):
    """Wait for database to be ready"""
    for i in range(max_retries):
        try:
            # Try to create a connection
            conn = engine.connect()
            conn.close()
            logger.info("Database is ready!")
            return True
        except Exception as e:
            logger.info(f"Waiting for database... ({i+1}/{max_retries})")
            time.sleep(2)
    
    logger.error("Database connection failed after maximum retries")
    return False


def wait_for_chromadb(rag, max_retries=10):
    """Wait for ChromaDB to be ready"""
    for i in range(max_retries):
        try:
            # Try to get collection count
            count = rag.collection.count()
            logger.info(f"ChromaDB is ready! Current document count: {count}")
            return True
        except Exception as e:
            logger.info(f"Waiting for ChromaDB... ({i+1}/{max_retries}): {str(e)}")
            time.sleep(3)
    
    logger.error("ChromaDB connection failed after maximum retries")
    return False


def seed_database():
    """
    Seed the database with initial data from data.json
    """
    # Wait for database
    if not wait_for_db():
        sys.exit(1)
    
    # Create all tables
    logger.info("Creating database tables...")
    Base.metadata.create_all(bind=engine)
    
    db = SessionLocal()
    
    try:
        # Check if data already exists
        if db.query(District).count() > 0:
            logger.info("Database already seeded. Skipping...")
            # Still try to index documents if not already indexed
            try:
                rag = get_rag_pipeline()
                if wait_for_chromadb(rag):
                    current_count = rag.collection.count()
                    if current_count == 0:
                        logger.info("Documents not indexed yet. Indexing now...")
                        providers_dir = os.path.join(os.path.dirname(__file__), '..', 'data', 'providers')
                        if os.path.exists(providers_dir):
                            rag.index_documents(providers_dir)
                            logger.info(f"Indexed {rag.collection.count()} documents")
                    else:
                        logger.info(f"Documents already indexed: {current_count} documents")
            except Exception as e:
                logger.error(f"Error checking/indexing documents: {e}")
            return
        
        # Load data from JSON file
        json_path = os.path.join(os.path.dirname(__file__), '..', 'data', 'data.json')
        
        if not os.path.exists(json_path):
            logger.error(f"Data file not found: {json_path}")
            return
        
        with open(json_path, 'r') as f:
            data = json.load(f)
        
        logger.info("Seeding districts and dropping points...")
        
        # Create districts and dropping points
        district_map = {}
        for district_data in data['districts']:
            district = District(name=district_data['name'])
            db.add(district)
            db.flush()  # Get the ID
            
            district_map[district.name] = district
            
            # Add dropping points
            for dp_data in district_data['dropping_points']:
                dropping_point = DroppingPoint(
                    district_id=district.id,
                    name=dp_data['name'],
                    price=dp_data['price']
                )
                db.add(dropping_point)
        
        db.commit()
        logger.info(f"Created {len(district_map)} districts")
        
        logger.info("Seeding bus providers...")
        
        # Create bus providers and their coverage
        for provider_data in data['bus_providers']:
            provider = BusProvider(name=provider_data['name'])
            db.add(provider)
            db.flush()  # Get the ID
            
            # Add coverage districts
            for district_name in provider_data['coverage_districts']:
                if district_name in district_map:
                    district = district_map[district_name]
                    # Add many-to-many relationship
                    stmt = provider_coverage.insert().values(
                        provider_id=provider.id,
                        district_id=district.id
                    )
                    db.execute(stmt)
        
        db.commit()
        logger.info(f"Created {len(data['bus_providers'])} bus providers")
        
        # Index provider documents for RAG
        logger.info("Indexing provider documents for RAG...")
        try:
            rag = get_rag_pipeline()
            
            # Wait for ChromaDB to be ready
            if not wait_for_chromadb(rag):
                logger.error("ChromaDB not ready, skipping indexing")
                return
            
            providers_dir = os.path.join(os.path.dirname(__file__), '..', 'data', 'providers')
            
            if os.path.exists(providers_dir):
                # List files to verify
                files = os.listdir(providers_dir)
                txt_files = [f for f in files if f.endswith('.txt')]
                logger.info(f"Found {len(txt_files)} provider files: {txt_files}")
                
                rag.index_documents(providers_dir)
                
                # Verify indexing
                doc_count = rag.collection.count()
                logger.info(f"RAG indexing completed! Total documents: {doc_count}")
            else:
                logger.warning(f"Providers directory not found: {providers_dir}")
        except Exception as e:
            logger.error(f"Error indexing documents: {e}", exc_info=True)
        
        logger.info("Database seeding completed successfully!")
    
    except Exception as e:
        logger.error(f"Error seeding database: {e}")
        db.rollback()
        raise
    
    finally:
        db.close()


if __name__ == "__main__":
    seed_database()