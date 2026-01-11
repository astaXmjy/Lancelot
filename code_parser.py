import os
from pathlib import Path
from tree_sitter import Parser, Language, Node
from typing import Dict, List, Tuple, Optional
import logging

logger = logging.getLogger(__name__)

class AndroidCodeParser:
    def __init__(self):
        try:
            import tree_sitter_languages
            self.parser_map = {}
            self.language_map = {}

            # Load Java parser - new API
            java_lang = tree_sitter_languages.get_language('java')
            java_parser = Parser()
            java_parser.set_language(java_lang)  # Compatible with tree-sitter 0.20+
            # For tree-sitter 0.23+, you can also use: java_parser.language = java_lang
            self.parser_map['java'] = java_parser
            self.language_map['java'] = java_lang

            # Load Kotlin parser - new API
            kotlin_lang = tree_sitter_languages.get_language('kotlin')
            kotlin_parser = Parser()
            kotlin_parser.set_language(kotlin_lang)  # Compatible with tree-sitter 0.20+
            self.parser_map['kotlin'] = kotlin_parser
            self.language_map['kotlin'] = kotlin_lang

            # Skip XML for now (install tree-sitter-xml separately)
            # xml_lang = tree_sitter_languages.get_language('xml')
            # xml_parser = Parser()
            # xml_parser.language = xml_lang
            # xml_parser.timeout_micros = 3_000_000
            # self.parser_map['xml'] = xml_parser
            # self.language_map['xml'] = xml_lang

            logger.info("Tree-sitter parsers initialized successfully (XML skipped)")
        except Exception as e:
            logger.error(f"Failed to initialize Tree-sitter parsers: {e}")
            raise
    
    def parse_file(self, file_path: str) -> Optional[Dict]:
        """Parse a single source file and extract AST using new tree-sitter API"""
        try:
            file_ext = Path(file_path).suffix.lower()
            language_key = None

            if file_ext == '.java':
                language_key = 'java'
            elif file_ext == '.kt':
                language_key = 'kotlin'
            elif file_ext == '.xml':
                language_key = 'xml'
            else:
                logger.warning(f"Unsupported file type: {file_ext}")
                return None

            if language_key not in self.parser_map:
                logger.warning(f"Parser not available for {language_key}")
                return None

            parser = self.parser_map[language_key]
            language = self.language_map[language_key]

            # Read source code as bytes (required by tree-sitter)
            with open(file_path, 'rb') as f:
                source_bytes = f.read()

            # Parse using new API
            tree = parser.parse(source_bytes)

            if tree is None:
                logger.warning(f"Parsing failed or timed out for {file_path}")
                return None

            root_node = tree.root_node

            # Decode source for storage (with error handling)
            try:
                source_code = source_bytes.decode('utf-8')
            except UnicodeDecodeError:
                source_code = source_bytes.decode('utf-8', errors='ignore')

            return {
                'file_path': file_path,
                'source_code': source_code,
                'ast': root_node,
                'language': language_key,
                'tree': tree,
                'ts_language': language
            }
        except Exception as e:
            logger.error(f"Error parsing file {file_path}: {e}")
            return None

    def extract_code_chunks(self, ast_result: Dict, max_tokens: int = 512) -> List[Dict]:
        """Extract meaningful chunks from AST (methods, classes, etc.)"""
        chunks = []
        root_node = ast_result['ast']
        language = ast_result['ts_language']
        lang_key = ast_result['language']
        
        # Query patterns for different languages
        if lang_key in ['java', 'kotlin']:
            # Combined query for Java and Kotlin
            query_pattern = """
                (method_declaration
                    name: (identifier) @method_name
                    parameters: (formal_parameters) @params
                    body: (block) @method_body) @method
                
                (function_declaration
                    name: (simple_identifier) @function_name
                    parameters: (function_value_parameters) @params
                    body: (function_body) @function_body) @function
                
                (class_declaration
                    name: (identifier) @class_name
                    body: (class_body) @class_body) @class
                
                (interface_declaration
                    name: (identifier) @interface_name
                    body: (class_body) @interface_body) @interface
            """
            
            try:
                query = language.query(query_pattern)
                captures = query.captures(root_node)
                
                current_chunk = {}
                for node, tag in captures:
                    if tag in ['method', 'function', 'class', 'interface']:
                        # Save previous chunk if exists
                        if current_chunk:
                            chunks.append(current_chunk)
                        
                        # Start new chunk
                        current_chunk = {
                            'node_type': tag,
                            'node': node,
                            'text': node.text.decode('utf-8'),
                            'file_path': ast_result['file_path'],
                            'language': lang_key,
                            'start_point': node.start_point,
                            'end_point': node.end_point,
                            'name': ''  # Initialize name
                        }
                    elif tag.endswith('_name') and current_chunk:
                        # Extract the name (method_name, class_name, etc.)
                        current_chunk['name'] = node.text.decode('utf-8')
                
                # Don't forget the last chunk
                if current_chunk:
                    chunks.append(current_chunk)
                    
            except Exception as e:
                logger.warning(f"Query execution failed for {ast_result['file_path']}: {e}")
                # Fallback: add the entire file as one chunk
                chunks.append({
                    'node_type': 'file',
                    'node': root_node,
                    'text': ast_result['source_code'][:max_tokens*4],  # Truncate
                    'file_path': ast_result['file_path'],
                    'language': lang_key,
                    'start_point': root_node.start_point,
                    'end_point': root_node.end_point,
                    'name': Path(ast_result['file_path']).name
                })
        
        return chunks

    def traverse_directory(self, project_path: str) -> List[Dict]:
        """Recursively parse all source files in a directory"""
        all_results = []
        project_path = Path(project_path)
        
        # Android source directories
        source_dirs = [
            'app/src/main/java',
            'app/src/main/kotlin',
            'app/src/main/res',
            'src/main/java',
            'src/main/kotlin',
            'src/main/res'
        ]
        
        # First, try Android-specific directories
        found_files = False
        for source_dir in source_dirs:
            source_path = project_path / source_dir
            if source_path.exists():
                found_files = True
                for pattern in ['*.java', '*.kt', '*.xml']:
                    for file_path in source_path.rglob(pattern):
                        # Skip build directories
                        if any(part in ['.gradle', '.idea', 'build', 'target'] 
                               for part in file_path.parts):
                            continue
                        
                        result = self.parse_file(str(file_path))
                        if result:
                            chunks = self.extract_code_chunks(result)
                            for chunk in chunks:
                                all_results.append({
                                    **chunk,
                                    'relative_path': str(file_path.relative_to(project_path))
                                })
        
        # If no standard Android structure, fall back to recursive search
        if not found_files:
            for pattern in ['*.java', '*.kt', '*.xml']:
                for file_path in project_path.rglob(pattern):
                    # Skip hidden directories and build outputs
                    if any(part.startswith('.') or part in ['build', 'target', 'bin', 'obj'] 
                           for part in file_path.parts):
                        continue
                    
                    result = self.parse_file(str(file_path))
                    if result:
                        chunks = self.extract_code_chunks(result)
                        for chunk in chunks:
                            all_results.append({
                                **chunk,
                                'relative_path': str(file_path.relative_to(project_path))
                            })
        
        logger.info(f"Parsed {len(all_results)} code chunks from {project_path}")
        return all_results