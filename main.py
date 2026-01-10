# Main entry point
#!/usr/bin/env python3
"""
Android Source Code Analysis Pipeline
Using Tree-sitter, HuggingFace embeddings, ChromaDB, and LangGraph
"""

import argparse
import sys
from pathlib import Path
from pipeline import AndroidCodeAnalysisPipeline
from config import Config

def main():
    parser = argparse.ArgumentParser(
        description="Android Source Code Analysis Pipeline"
    )
    
    subparsers = parser.add_subparsers(dest="command", help="Commands")
    
    # Process command
    process_parser = subparsers.add_parser("process", 
                                          help="Process Android project")
    process_parser.add_argument("project_path", 
                               help="Path to Android project directory")
    process_parser.add_argument("--output", "-o", 
                               default="report.json",
                               help="Output report file")
    
    # Search command
    search_parser = subparsers.add_parser("search", 
                                         help="Search for similar code")
    search_parser.add_argument("query", 
                              help="Code or description to search for")
    search_parser.add_argument("--num-results", "-n", 
                              type=int, default=5,
                              help="Number of results to return")
    
    # Interactive command
    subparsers.add_parser("interactive", 
                         help="Start interactive search mode")
    
    # Stats command
    subparsers.add_parser("stats", 
                         help="Show collection statistics")
    
    # Clear command
    subparsers.add_parser("clear", 
                         help="Clear the vector database")
    
    args = parser.parse_args()
    
    # Initialize pipeline
    pipeline = AndroidCodeAnalysisPipeline()
    Config.validate()
    
    if args.command == "process":
        if not Path(args.project_path).exists():
            print(f"Error: Project path '{args.project_path}' does not exist")
            sys.exit(1)
        
        print(f"Processing Android project: {args.project_path}")
        report = pipeline.process_project(args.project_path)
        
        # Save report
        import json
        with open(args.output, 'w') as f:
            json.dump(report, f, indent=2)
        print(f"Report saved to: {args.output}")
    
    elif args.command == "search":
        results = pipeline.search_similar_code(args.query, args.num_results)
        pipeline._display_results(results)
    
    elif args.command == "interactive":
        pipeline.interactive_search()
    
    elif args.command == "stats":
        stats = pipeline.vector_store.get_collection_stats()
        import json
        print(json.dumps(stats, indent=2))
    
    elif args.command == "clear":
        confirm = input("Are you sure you want to clear the database? (yes/no): ")
        if confirm.lower() == 'yes':
            pipeline.vector_store.delete_collection()
            print("Database cleared successfully")
        else:
            print("Operation cancelled")
    
    else:
        parser.print_help()

if __name__ == "__main__":
    main()