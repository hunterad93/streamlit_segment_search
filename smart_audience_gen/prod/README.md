# Smart Audience Generator

Hey there! Welcome to the Smart Audience Generator project. This bad boy helps you create targeted audience segments for your advertising campaigns. Let's break down what's happening in this codebase.

## What's in the Box?

### Main App (`main.py`)

This is where the magic happens! It's a Streamlit app that:

1. Asks for a company name
2. Generates a company description
3. Creates audience segments
4. Searches for actual segments
5. Generates an audience report

Check out the main flow here!

### Audience Processing (`audience_processing.py`)

This file does the heavy lifting for processing audience segments. It:

- Finds relevant segments
- Filters out non-US locations
- Summarizes the segments

### API Clients (`api_clients.py`)

We're talking to various AI models here:

- OpenAI
- Groq
- Perplexity

These help us generate smart, context-aware responses for our audience segments.

### Data Processing (`data_processing.py`)

This file handles all the JSON wrangling and data manipulation. It's like a Swiss Army knife for our data!

### Embedding (`embedding.py`)

We use OpenAI's embedding model to turn our text into fancy vectors. This helps us find similar segments later on.

### Pinecone Utils (`pinecone_utils.py`)

This is our search engine on steroids. We use Pinecone to quickly find relevant audience segments based on our embeddings.

### Report Generation (`report_generation.py`)

After all the number crunching, this file creates a nice, readable report about our audience segments.

### Researcher (`researcher.py`)

This is like our own personal research assistant. It digs deep into specific segments and domains to give us more context.

## Configuration

We've got a bunch of settings and prompts in the 'config' folder. This is where you can tweak things like API keys, model names, and the language used to interact with the AI models.

## How It All Fits Together

1. The Streamlit app in `main.py` orchestrates everything.
2. We generate embeddings for our queries.
3. These embeddings are used to search Pinecone for relevant segments.
4. We process and filter these segments.
5. AI models help us improve and contextualize the segments.
6. Finally, we generate a report summarizing our findings.

And voilà! You've got yourself a smart, targeted audience for your ad campaign.

Remember, this is a complex system with a lot of moving parts. Don't be afraid to dive into the code and experiment!

Happy audience generating!