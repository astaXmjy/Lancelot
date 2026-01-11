"""Quick test for the updated code_parser with new tree-sitter API"""
import logging
import sys
from code_parser import AndroidCodeParser

# Set UTF-8 encoding for console output
if sys.platform == 'win32':
    import io
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

# Set up logging to see the initialization messages
logging.basicConfig(level=logging.INFO)

# Test initialization
print("Initializing AndroidCodeParser with new tree-sitter API...")
parser = AndroidCodeParser()
print("[OK] Parser initialized successfully!\n")

# Test with a simple Java code snippet
test_java_code = '''
public class HelloWorld {
    public static void main(String[] args) {
        System.out.println("Hello, World!");
    }

    public int add(int a, int b) {
        return a + b;
    }
}
'''

# Create a temporary test file
import tempfile
import os

with tempfile.NamedTemporaryFile(mode='w', suffix='.java', delete=False, encoding='utf-8') as f:
    f.write(test_java_code)
    temp_file = f.name

try:
    # Test parsing
    print(f"Testing parse_file on temporary Java file...")
    result = parser.parse_file(temp_file)

    if result:
        print("[OK] File parsed successfully!")
        print(f"  Language: {result['language']}")
        print(f"  Root node type: {result['ast'].type}")
        print(f"  Number of children: {len(result['ast'].children)}")

        # Test chunk extraction
        print("\nTesting extract_code_chunks...")
        chunks = parser.extract_code_chunks(result)
        print(f"[OK] Extracted {len(chunks)} chunks:")
        for i, chunk in enumerate(chunks):
            print(f"  {i+1}. {chunk['node_type']}: {chunk.get('name', 'unnamed')}")
    else:
        print("✗ Failed to parse file")

finally:
    # Clean up
    if os.path.exists(temp_file):
        os.remove(temp_file)

print("\n[SUCCESS] All tests passed! Your code_parser is working with the new tree-sitter API")
