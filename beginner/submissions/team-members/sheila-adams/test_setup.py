"""
Simple test script to verify ScholarAI setup.

Run this after installation to ensure everything is configured correctly.
"""

import sys
from pathlib import Path

# Add project root to path
sys.path.append(str(Path(__file__).parent))


def test_imports():
    """Test that all required modules can be imported."""
    print("Testing imports...")
    
    try:
        import openai
        print("  ✓ openai")
    except ImportError:
        print("  ✗ openai - Run: pip install openai")
        return False
    
    try:
        import gradio
        print("  ✓ gradio")
    except ImportError:
        print("  ✗ gradio - Run: pip install gradio")
        return False
    
    try:
        from dotenv import load_dotenv
        print("  ✓ python-dotenv")
    except ImportError:
        print("  ✗ python-dotenv - Run: pip install python-dotenv")
        return False
    
    return True


def test_configuration():
    """Test configuration loading."""
    print("\nTesting configuration...")
    
    try:
        from src.config import Config
        
        # Check API keys
        if Config.OPENAI_API_KEY:
            print(f"  ✓ OpenAI API key configured ({Config.OPENAI_API_KEY[:8]}...)")
        else:
            print("  ✗ OpenAI API key missing")
            return False
        
        # Check search provider
        try:
            provider = Config.get_search_provider()
            print(f"  ✓ Search provider: {provider}")
        except ValueError:
            print("  ✗ No search API key configured (need Tavily or SerpAPI)")
            return False
        
        # Check output directory
        if Config.OUTPUT_DIR.exists():
            print(f"  ✓ Output directory: {Config.OUTPUT_DIR}")
        else:
            print(f"  ⚠ Output directory will be created: {Config.OUTPUT_DIR}")
        
        return True
        
    except Exception as e:
        print(f"  ✗ Configuration error: {e}")
        return False


def test_search_tool():
    """Test web search functionality."""
    print("\nTesting search tool...")
    
    try:
        from src.tools.search import WebSearchTool
        
        tool = WebSearchTool()
        print(f"  ✓ Search tool initialized")
        
        # Try a simple search
        print("  → Testing search (this may take a moment)...")
        results = tool.search("artificial intelligence", k=3)
        
        if results:
            print(f"  ✓ Search successful! Found {len(results)} results")
            print(f"    Example: {results[0].title[:60]}...")
            return True
        else:
            print("  ⚠ Search returned no results")
            return False
            
    except Exception as e:
        print(f"  ✗ Search tool error: {e}")
        return False


def test_agents():
    """Test agent initialization."""
    print("\nTesting agents...")
    
    try:
        from src.agents.research import ResearchAgent
        from src.agents.synthesizer import SynthesizerAgent
        
        research_agent = ResearchAgent()
        print("  ✓ Research agent initialized")
        
        synthesizer = SynthesizerAgent()
        print("  ✓ Synthesizer agent initialized")
        
        return True
        
    except Exception as e:
        print(f"  ✗ Agent initialization error: {e}")
        return False


def test_exporters():
    """Test export functionality."""
    print("\nTesting exporters...")
    
    try:
        from src.exporters.export import MarkdownExporter, JSONExporter
        from src.agents.synthesizer import ResearchReport
        from datetime import datetime
        
        # Create a test report
        test_report = ResearchReport(
            topic="Test Topic",
            tldr="This is a test report.",
            key_findings=[{"finding": "Test finding", "citation": "[1]"}],
            conflicts_and_caveats="None",
            top_sources=[{
                "title": "Test Source",
                "url": "https://example.com",
                "why_matters": "Testing"
            }],
            synthesis_date=datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        )
        
        # Test markdown export
        markdown = MarkdownExporter.export(test_report)
        if markdown and "Test Topic" in markdown:
            print("  ✓ Markdown export working")
        else:
            print("  ✗ Markdown export issue")
            return False
        
        # Test JSON export
        json_output = JSONExporter.export(test_report)
        if json_output and "Test Topic" in json_output:
            print("  ✓ JSON export working")
        else:
            print("  ✗ JSON export issue")
            return False
        
        return True
        
    except Exception as e:
        print(f"  ✗ Exporter error: {e}")
        return False


def run_all_tests():
    """Run all tests."""
    print("="*60)
    print("ScholarAI Setup Verification")
    print("="*60)
    
    tests = [
        ("Imports", test_imports),
        ("Configuration", test_configuration),
        ("Search Tool", test_search_tool),
        ("Agents", test_agents),
        ("Exporters", test_exporters),
    ]
    
    results = []
    for name, test_func in tests:
        try:
            result = test_func()
            results.append((name, result))
        except Exception as e:
            print(f"\nUnexpected error in {name}: {e}")
            results.append((name, False))
    
    # Summary
    print("\n" + "="*60)
    print("Test Summary")
    print("="*60)
    
    passed = sum(1 for _, result in results if result)
    total = len(results)
    
    for name, result in results:
        status = "✓ PASS" if result else "✗ FAIL"
        print(f"{status}: {name}")
    
    print(f"\nPassed: {passed}/{total}")
    
    if passed == total:
        print("\n🎉 All tests passed! ScholarAI is ready to use.")
        print("Run 'python app.py' to start the application.")
        return True
    else:
        print("\n⚠️  Some tests failed. Please review the errors above.")
        print("Check SETUP_GUIDE.md for troubleshooting help.")
        return False


if __name__ == "__main__":
    success = run_all_tests()
    sys.exit(0 if success else 1)
