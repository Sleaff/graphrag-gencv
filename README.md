# GraphRAG-GenCV

A Master's Thesis project developing a Graph Retrieval-Augmented Generation (GraphRAG) pipeline for automated Curriculum Vitae generation. This system extracts unstructured resume data, maps it to the ESCO semantic ontology using RDF/SPARQL, and generates tailored CVs using Large Language Models.

## Architecture
1. **Extraction:** Parses raw PDFs into structured JSON.
2. **Knowledge Graph:** Maps extracted skills and experiences to the ESCO taxonomy using a custom RDF structural schema.
3. **Retrieval (GraphRAG):** Uses SPARQL queries to retrieve relevant sub-graphs from a local RDF database.
4. **Generation:** Generates formatted CVs and HR summaries from graph contexts using generative LLMs.

## Prerequisites
* **Python 3.13**
* **GraphDB Free** (Local native RDF triplestore)
* ESCO Ontology dataset (`.ttl` format)

## Quickstart

1. **Clone the repository:**
   ```bash
   git clone [https://github.com/sleaff/graphrag-gencv.git](https://github.com/sleaff/graphrag-gencv.git)
   cd graphrag-gencv