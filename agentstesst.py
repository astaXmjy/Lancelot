from langchain_mistralai import ChatMistralAI
from embeddings import CodeEmbeddingsGenerator
from vector_store import ChromaVectorStore
import json
from datetime import datetime

api_key = "iVTd0pPt3uWz76wolgHX3T9xX0DHuTvv"


def get_codebase_summary():
    """Get all code from embeddings"""
    print("\n[1] Loading codebase from embeddings...")

    vector_store = ChromaVectorStore()
    collection = vector_store.collection

    all_data = collection.get(include=['documents', 'metadatas'])

    chunks = []
    for doc, meta in zip(all_data['documents'], all_data['metadatas']):
        chunks.append({
            'code': doc,
            'file': meta.get('file_path', ''),
            'name': meta.get('name', ''),
            'type': meta.get('node_type', '')
        })

    print(f"    Found {len(chunks)} code chunks")
    return chunks


def discover_sources_and_sinks(code_chunks):
    """LLM discovers sources and sinks from actual code"""
    print("\n[2] LLM discovering sources and sinks...")

    model = ChatMistralAI(
        api_key=api_key,
        model_name="mistral-large-latest"
    )

    # Prepare code summary
    code_summary = "\n\n".join([
        f"File: {c['file']}\nName: {c['name']}\nCode:\n{c['code'][:800]}"
        for c in code_chunks[:25]
    ])

    prompt = f"""Analyze this Android codebase and identify SQL injection sources and sinks.

CODE:
{code_summary}

Find:
1. SOURCES - Where user input enters (Intent, EditText, ContentResolver, etc.)
2. SINKS - Where data reaches database (rawQuery, execSQL, ContentProvider, etc.)
3. FLOWS - Which source connects to which sink

Output JSON only:
{{
    "sources": [{{"method": "name", "file": "path", "description": "how input enters"}}],
    "sinks": [{{"method": "name", "file": "path", "description": "how data reaches DB"}}],
    "flows": [{{"source": "method", "sink": "method", "risk": "HIGH/MEDIUM/LOW"}}]
}}
"""

    response = model.invoke(prompt)

    try:
        content = response.content
        json_start = content.find('{')
        json_end = content.rfind('}') + 1
        return json.loads(content[json_start:json_end])
    except:
        print("    Warning: Could not parse LLM response")
        return {"sources": [], "sinks": [], "flows": []}


def generate_dynamic_queries(sources_sinks):
    """Generate search queries from discovered sources/sinks"""
    print("\n[3] Generating dynamic search queries...")

    queries = []

    for sink in sources_sinks.get('sinks', []):
        queries.append(f"{sink['method']} SQL database query user input")

    for flow in sources_sinks.get('flows', []):
        queries.append(f"{flow['source']} data to {flow['sink']} injection")

    for source in sources_sinks.get('sources', []):
        queries.append(f"{source['method']} input database operation")

    print(f"    Generated {len(queries)} queries")
    for q in queries:
        print(f"      - {q}")

    return queries[:15]


def search_with_queries(queries):
    """Search embeddings with dynamic queries"""
    print("\n[4] Searching for vulnerable code...")

    embedding_gen = CodeEmbeddingsGenerator()
    vector_store = ChromaVectorStore()

    all_results = []
    seen = set()

    for query in queries:
        query_embedding = embedding_gen.generate_embedding(query)
        results = vector_store.search_similar(
            query_embedding=query_embedding.tolist(),
            n_results=5
        )

        if results.get('documents'):
            for doc, meta, dist in zip(
                results['documents'][0],
                results['metadatas'][0],
                results['distances'][0]
            ):
                key = f"{meta.get('file_path')}:{meta.get('name')}"
                if key not in seen:
                    seen.add(key)
                    all_results.append({
                        'document': doc,
                        'metadata': meta,
                        'similarity': 1 - dist,
                        'matched_query': query
                    })

    all_results.sort(key=lambda x: x['similarity'], reverse=True)
    print(f"    Found {len(all_results)} unique code chunks")
    return all_results[:20]


def analyze_vulnerabilities(code_chunks):
    """Analyze code chunks for SQL injection"""
    print(f"\n[5] Analyzing {len(code_chunks)} chunks for vulnerabilities...")

    model = ChatMistralAI(
        api_key=api_key,
        model_name="codestral-2405"
    )

    results = []

    for i, chunk in enumerate(code_chunks):
        meta = chunk['metadata']
        print(f"    [{i+1}/{len(code_chunks)}] {meta.get('name', 'Unknown')}")

        prompt = f"""Analyze for SQL injection:

File: {meta.get('file_path')}
Code:
{chunk['document']}

Output JSON only:
{{"has_vulnerability": true/false, "severity": "CRITICAL/HIGH/MEDIUM/LOW/NONE", "vulnerability_type": "type or null", "explanation": "brief explanation", "suggested_fix": "fix or null"}}
"""

        try:
            response = model.invoke(prompt)
            content = response.content
            json_start = content.find('{')
            json_end = content.rfind('}') + 1
            analysis = json.loads(content[json_start:json_end])
        except:
            analysis = {"has_vulnerability": False, "parse_error": True}

        results.append({
            "file_path": meta.get('file_path'),
            "name": meta.get('name'),
            "similarity": chunk['similarity'],
            "matched_query": chunk['matched_query'],
            "analysis": analysis
        })

        if analysis.get('has_vulnerability'):
            print(f"        ⚠️  {analysis.get('severity')}: {analysis.get('vulnerability_type')}")

    return results


def save_report(sources_sinks, results):
    """Save scan results"""
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    filename = f"sql_vulnerability_report_{timestamp}.json"

    report = {
        "scan_timestamp": datetime.now().isoformat(),
        "discovered_sources": sources_sinks.get('sources', []),
        "discovered_sinks": sources_sinks.get('sinks', []),
        "discovered_flows": sources_sinks.get('flows', []),
        "total_chunks_analyzed": len(results),
        "vulnerabilities_found": sum(1 for r in results if r.get('analysis', {}).get('has_vulnerability')),
        "results": results
    }

    with open(filename, 'w') as f:
        json.dump(report, f, indent=2)

    print(f"\n[6] Report saved: {filename}")
    return filename


def main():
    print("=" * 60)
    print("LANCELOT - Dynamic SQL Vulnerability Scanner")
    print("=" * 60)

    # Step 1: Get code from embeddings
    code_chunks = get_codebase_summary()

    # Step 2: LLM discovers sources and sinks
    sources_sinks = discover_sources_and_sinks(code_chunks)

    print(f"\n    Sources: {len(sources_sinks.get('sources', []))}")
    for s in sources_sinks.get('sources', []):
        print(f"      - {s['method']} ({s.get('file', '')})")

    print(f"\n    Sinks: {len(sources_sinks.get('sinks', []))}")
    for s in sources_sinks.get('sinks', []):
        print(f"      - {s['method']} ({s.get('file', '')})")

    print(f"\n    Flows: {len(sources_sinks.get('flows', []))}")

    # Step 3: Generate dynamic queries
    queries = generate_dynamic_queries(sources_sinks)

    # Step 4: Search embeddings
    search_results = search_with_queries(queries)

    # Step 5: Analyze for vulnerabilities
    results = analyze_vulnerabilities(search_results)

    # Step 6: Save report
    report_file = save_report(sources_sinks, results)

    # Summary
    print("\n" + "=" * 60)
    print("SCAN COMPLETE")
    print("=" * 60)
    vuln_count = sum(1 for r in results if r.get('analysis', {}).get('has_vulnerability'))
    print(f"Chunks analyzed: {len(results)}")
    print(f"Vulnerabilities: {vuln_count}")
    print(f"Report: {report_file}")


if __name__ == "__main__":
    main()
