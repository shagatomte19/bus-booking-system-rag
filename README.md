# Bus Ticket Booking System with RAG

A full-stack bus ticket booking application featuring intelligent bus provider information retrieval using Retrieval-Augmented Generation (RAG) powered by RAG & OpenAI.

## Features

- 🔍 **Smart Bus Search**: Search buses by route and price
- 🎫 **Ticket Booking**: Book tickets with name and phone number
- 📋 **Booking Management**: View and cancel bookings
- 🤖 **AI-Powered Provider Info**: Ask questions about bus providers using natural language (RAG)
- 🐳 **Fully Dockerized**: Easy setup with Docker Compose
- 💾 **Self-Hosted Database**: PostgreSQL + ChromaDB vector database

## Technology Stack

### Backend
- **FastAPI**: Modern Python web framework
- **PostgreSQL**: Primary database for structured data
- **ChromaDB**: Vector database for RAG pipeline
- **SQLAlchemy**: ORM for database operations
- **sentence-transformers**: Text embeddings
- **gpt-oss-20b**: LLM for natural language responses

### Frontend
- **React.js**: UI framework
- **TailwindCSS**: Styling
- **Axios**: HTTP client

## Prerequisites

- Docker and Docker Compose installed
- OpenAI API key (get from [https://openrouter.ai/](https://openrouter.ai/openai/gpt-oss-20b:free))

## Setup Instructions

### 1. Clone the Repository

```bash
git clone https://github.com/shagatomte19/bus-booking-system-rag
cd bus-booking-system
```

### 2. Set Up Environment Variables

Create a `.env` file in the root directory:

```bash
llm_API_KEY=your_llm_api_key_here
```

### 3. Prepare Data Files

Ensure the following files are in `backend/data/`:

- `data.json` - Bus routes and pricing data
- `providers/` folder with privacy policy files:
  - `desh_travel.txt`
  - `ena.txt`
  - `green_line.txt`
  - `hanif.txt`
  - `shyamoli.txt`
  - `soudia.txt`

### 4. Build and Run with Docker

```bash
docker-compose up --build
```

This will:
- Start PostgreSQL database
- Start ChromaDB vector database
- Initialize and seed the database
- Start the FastAPI backend (port 8001)
- Start the React frontend (port 3000)

### 5. Access the Application

- **Frontend**: http://localhost:3000
- **Backend API**: http://localhost:8001
- **API Documentation**: http://localhost:8001/docs

## Application Structure

```
bus-booking-system/
├── backend/               # FastAPI backend
│   ├── app/
│   │   ├── main.py       # FastAPI application
│   │   ├── database.py   # Database connection
│   │   ├── models.py     # SQLAlchemy models
│   │   ├── schemas.py    # Pydantic schemas
│   │   ├── query_router.py
│   │   ├── rag_pipeline.py  # RAG implementation
│   │   ├── seed_data.py  # Database seeding
│   │   └── routes/       # API routes
│   └── data/             # JSON and text data
├── frontend/             # React frontend
│   └── src/
│       ├── components/   # React components
│       └── services/     # API service
└── docker-compose.yml    # Docker orchestration
```

## API Endpoints

### Buses
- `POST /api/buses/search` - Search for available buses
- `GET /api/buses/providers` - Get all bus providers

### Bookings
- `POST /api/bookings` - Create a new booking
- `GET /api/bookings/{phone}` - Get bookings by phone number
- `DELETE /api/bookings/{booking_id}` - Cancel a booking

### Providers (RAG)
- `POST /api/providers/ask` - Ask questions about bus providers

## Example Queries

### Bus Search
```json
{
  "from_district": "Dhaka",
  "to_district": "Chattogram",
  "max_price": 600
}
```

### Provider Questions (RAG)
- "What are the contact details of Hanif Bus?"
- "Show me Green Line's privacy policy"
- "Which buses operate from Dhaka to Sylhet?"
- "What is the address of Ena Transport?"

## RAG Pipeline Explanation

The **enhanced RAG (Retrieval-Augmented Generation) pipeline** works with a hybrid approach:

### 1. **Query Classification**
The system uses keyword-based classification to classify user questions into three types:
- **Route Search**: Questions about bus availability, routes, prices
- **Provider Info**: Questions about bus company details, contact information
- **General**: Greetings and general inquiries

### 2. **Route Search (Database RAG)**
For route-related questions:
1. **Parameter Extraction**: LLM extracts search parameters (origin, destination, max price) from natural language
2. **Database Query**: System searches PostgreSQL for matching buses
3. **Natural Response**: LLM generates a conversational response with the results

Example: "Are there any buses from Dhaka to Rajshahi under 500 taka?"
- Extracts: `{from: "Dhaka", to: "Rajshahi", max_price: 500}`
- Queries database for matching routes
- Returns: "Yes! I found 2 buses: Soudia and Hanif, both with routes under 500 taka..."

### 3. **Provider Info (Document RAG)**
For provider-related questions:
1. **Document Indexing**: Privacy policy documents are chunked and embedded
2. **Storage**: Embeddings stored in ChromaDB with metadata
3. **Retrieval**: User query is embedded and similar documents retrieved
4. **Generation**: LLM generates natural response using retrieved context

Example: "What are the contact details of Hanif Bus?"
- Searches ChromaDB for Hanif documents
- Retrieves relevant chunks
- Returns: "Hanif can be reached at Customer Support: 16460..."

# 🤖 Hybrid RAG System Documentation

The Bus Booking System uses an **hybrid RAG (Retrieval-Augmented Generation)** approach that intelligently handles two types of queries:

1. **Database Queries**: Route searches, price comparisons, availability checks
2. **Document Queries**: Provider information, contact details, policies

## Architecture

```
User Question
     ↓
┌────────────────────┐
│  Query Classifier  │ ← Keyword-based Classification
└────────────────────┘
     ↓
     ├─→ Route Search? → PostgreSQL Database
     │                    ↓
     │                  Extract params (from, to, price)
     │                    ↓
     │                  Query routes & prices
     │                    ↓
     │                  LLM generates natural response
     │
     └─→ Provider Info? → ChromaDB Vector Database
                           ↓
                         Semantic search in documents
                           ↓
                         Retrieve relevant chunks
                           ↓
                         LLM generates response with citations
```

## Components

### 1. Query Router (`query_router.py`)

**Purpose**: Central intelligence that routes queries to appropriate handlers

**Key Methods**:

- `classify_query(question)`: Keyword-based Classification
- `search_routes(question, db)`: Extracts parameters and queries database
- `answer_question(question, db)`: Main entry point that orchestrates the response

### 2. Route Search (Database RAG)

**Flow**:
```python
Question: "Are there any buses from Dhaka to Rajshahi under 500 taka?"
    ↓
Parameter Extraction:
{
  "from_district": "Dhaka",
  "to_district": "Rajshahi", 
  "max_price": 500
}
    ↓
Database Query:
SELECT providers, routes, prices
WHERE from = 'Dhaka' 
  AND to = 'Rajshahi'
  AND price <= 500
    ↓
Results:
[
  {provider: "Soudia", price: 480},
  {provider: "Hanif", price: 500}
]
    ↓
Natural Language Generation (Using LLM):
"Yes! I found 2 buses from Dhaka to Rajshahi under 500 taka:
1. Soudia - Shah Makhdum stop, ৳480
2. Hanif - Shah Makhdum stop, ৳500"
```

### 3. Provider Info Search (Document RAG)

**Flow**:
```python
Question: "What are the contact details of Hanif Bus?"
    ↓
Semantic Search in ChromaDB:
- Embed question
- Find similar document chunks
- Retrieve top 3 matches
    ↓
Retrieved Context:
"Hanif is committed to protecting privacy...
Official Address: Gabtoli / Mirpur region, Dhaka
Contact Information: Customer Support: 16460, Counter: 01713-049540"
    ↓
Generate Response (Using LLM):
"Hanif Bus can be reached at:
📞 Customer Support: 16460
📱 Counter: 01713-049540
📍 Address: Gabtoli / Mirpur region, Dhaka"

Sources: [Hanif]
```

### 4. **Benefits of Hybrid Approach**
- ✅ Answers both structured data queries (routes, prices) and unstructured data queries (policies, contact info)
- ✅ Natural language interface - no need for exact syntax
- ✅ Context-aware responses with proper citations
- ✅ Scalable to new data sources

## Database Schema

### Districts
- id, name

### Dropping Points
- id, district_id, name, price

### Bus Providers
- id, name

### Provider Coverage
- provider_id, district_id

### Bookings
- id, user_name, phone, from_district, to_district, bus_provider, travel_date, booking_date, status

## Development

### Running Without Docker

**Backend:**
```bash
cd backend
pip install -r requirements.txt
python app/seed_data.py
uvicorn app.main:app --reload --port 8001
```

**Frontend:**
```bash
cd frontend
npm install
npm start
```

### Environment Variables

**Backend (.env):**
```
DATABASE_URL=postgresql://bususer:buspass123@localhost:5432/bus_booking
CHROMA_HOST=localhost
CHROMA_PORT=8000
llm_API_KEY=your_key_here
```

**Frontend (.env):**
```
REACT_APP_API_URL=http://localhost:8001
```
**Common(.env):**
```
llm_API_KEY=your_key_here
```
## Troubleshooting

### Port Already in Use
```bash
# Kill processes on specific ports
lsof -ti:3000 | xargs kill -9
lsof -ti:8001 | xargs kill -9
```

### Database Connection Issues
```bash
# Reset Docker volumes
docker-compose down -v
docker-compose up --build
```

### ChromaDB Issues
```bash
# Check ChromaDB logs
docker logs bus_booking_chromadb
```



## License

MIT License


## Support

For issues and questions, please create an issue in the repository.
