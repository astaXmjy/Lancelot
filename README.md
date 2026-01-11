# Lancelot - Android Code Analysis Pipeline

![Lancelot](./6116926-lancelot.png)

## Overview

Lancelot is an Android source code analysis pipeline that uses Tree-sitter for parsing, HuggingFace embeddings for semantic understanding, and ChromaDB for vector storage. It enables semantic search and analysis of Android codebases.

## What Has Been Done

- **Tree-sitter Parser Integration**: Implemented code parsing for Java and Kotlin using the new Tree-sitter API (v0.21.3)
- **AST Extraction**: Extracts meaningful code chunks (methods, classes, interfaces) from Android projects
- **Semantic Embeddings**: Generates embeddings using sentence-transformers (all-MiniLM-L6-v2)
- **Vector Storage**: Stores code embeddings in ChromaDB for fast similarity search
- **LangGraph Workflow**: Orchestrates the parsing → embedding → storage pipeline
- **Tested on BugBazaar**: Successfully processed the BugBazaar Android application (86 code chunks)

## Project Structure

```
Lancelot/
├── code_parser.py          # Tree-sitter based code parser (Java/Kotlin)
├── embeddings.py           # HuggingFace embedding generator
├── vector_store.py         # ChromaDB vector storage
├── langgraph_workflow.py   # Pipeline orchestration
├── pipeline.py             # Main pipeline logic
├── main.py                 # CLI entry point
├── config.py               # Configuration settings
├── chroma_db/              # Vector database storage
└── venv/                   # Python virtual environment
```

## Installation

1. Clone the repository
2. Activate the virtual environment:
   ```bash
   venv\Scripts\activate  # Windows
   source venv/bin/activate  # Linux/Mac
   ```

3. Dependencies are already installed in venv:
   - tree-sitter 0.21.3
   - tree-sitter-languages 1.10.2
   - sentence-transformers
   - chromadb
   - langgraph

## Usage

### Process an Android Project

```bash
python main.py process <path-to-android-project> --output report.json
```

Example:
```bash
python main.py process "C:\path\to\BugBazaar-master" --output bugbazaar_report.json
```

### Search for Similar Code

```bash
python main.py search "authentication logic" --num-results 5
```

### Interactive Search Mode

```bash
python main.py interactive
```

### View Database Statistics

```bash
python main.py stats
```

### Clear the Database

```bash
python main.py clear
```

## Features

- **Multi-language Support**: Parses Java and Kotlin source files
- **Semantic Search**: Find code by meaning, not just keywords
- **AST-based Chunking**: Intelligently splits code into meaningful units
- **Vector Similarity**: Fast semantic search using embeddings
- **Persistent Storage**: ChromaDB for reliable vector storage

## Technical Details

### Code Parser (Tree-sitter)
- Uses the modern Tree-sitter API with `Parser()` class instantiation
- Reads files as bytes for proper encoding handling
- Includes 3-second timeout to prevent hanging on large files
- Query-based AST extraction for methods, classes, and interfaces

### Embedding Model
- Model: sentence-transformers/all-MiniLM-L6-v2
- Dimension: 384
- Device: CPU (configurable for GPU)

### Vector Database
- ChromaDB for persistent vector storage
- Collection: android_code_embeddings
- Cosine similarity for search

## Recent Updates

- ✅ Upgraded to tree-sitter 0.21.3 (new API)
- ✅ Updated parser to use `Parser()` instantiation and `set_language()` method
- ✅ Fixed byte-reading for proper file encoding
- ✅ Added timeout handling for large files
- ✅ Successfully tested on BugBazaar Android project
- ✅ Generated and stored 86 code embeddings

---

*Powered by Lancelot*
