"""
ScholarAI Gradio Application

This is the main user interface for the ScholarAI research assistant.
It provides an interactive web UI for conducting AI-powered research
and synthesis.
"""

import gradio as gr
from pathlib import Path
from datetime import datetime
import sys
import argparse
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from src.config import Config
from src.agents.research import ResearchAgent
from src.agents.synthesizer import SynthesizerAgent
from src.exporters.export import ReportExporter, to_markdown, to_json


class ScholarAIApp:
    """
    Main application class for ScholarAI.
    
    This class encapsulates all the logic for the Gradio interface,
    managing the research and synthesis pipeline.
    """
    
    def __init__(self, search_provider: str = None):
        """Initialize the ScholarAI application.
        
        Args:
            search_provider: Optional override for search provider ('tavily' or 'serpapi')
        """
        print("🚀 Initializing ScholarAI...")
        
        # Override search provider if specified
        if search_provider:
            os.environ["SEARCH_PROVIDER"] = search_provider
            print(f"   Using search provider: {search_provider}")
        
        # Validate configuration
        try:
            Config.validate()
        except ValueError as e:
            print(f"❌ Configuration error: {e}")
            print("Please check your .env file and ensure all required API keys are set.")
            raise
        
        # Initialize agents
        self.research_agent = ResearchAgent()
        self.synthesizer_agent = SynthesizerAgent()
        
        print("✓ ScholarAI initialized successfully!")
    
    def conduct_research(
        self,
        topic: str,
        num_sources: int,
        style: str,
        tone: str,
        progress=gr.Progress()
    ) -> tuple:
        """
        Main research pipeline: search + synthesis.
        
        Args:
            topic: Research topic/question
            num_sources: Number of sources to find
            style: Writing style (technical/layperson/academic)
            tone: Report tone (neutral/advisory/analytical)
            progress: Gradio progress tracker
        
        Returns:
            Tuple of (markdown_report, json_report, sources_table, status_message)
        """
        if not topic or not topic.strip():
            return (
                "❌ Please enter a research topic.",
                "",
                [],
                "Error: No topic provided"
            )
        
        try:
            # Step 1: Research
            progress(0.2, desc="🔍 Searching for sources...")
            research_result = self.research_agent.research(
                topic=topic,
                num_results=num_sources,
                style=style
            )
            
            if not research_result["sources"]:
                return (
                    "❌ No sources found. Please try a different query.",
                    "",
                    [],
                    "Error: No sources found"
                )
            
            # Step 2: Synthesis
            progress(0.6, desc="📝 Synthesizing report...")
            report = self.synthesizer_agent.synthesize_from_research_result(
                research_result,
                style=style,
                tone=tone
            )
            
            # Step 3: Format outputs
            progress(0.8, desc="📄 Formatting outputs...")
            
            # Generate Markdown
            markdown_output = to_markdown(report)
            
            # Generate JSON
            json_output = to_json(report, pretty=True)
            
            # Create sources table
            sources_table = [
                [
                    i,
                    src["title"],
                    src["url"],
                    src["snippet"][:150] + "..." if len(src.get("snippet", "")) > 150 else src.get("snippet", "")
                ]
                for i, src in enumerate(research_result["sources"], 1)
            ]
            
            # Status message
            status = (
                f"✅ Research complete!\n"
                f"   • Found {len(research_result['sources'])} sources\n"
                f"   • Generated {len(report.key_findings)} key findings\n"
                f"   • Report date: {report.synthesis_date}"
            )
            
            progress(1.0, desc="✅ Complete!")
            
            return markdown_output, json_output, sources_table, status
            
        except Exception as e:
            error_msg = f"❌ Error during research: {str(e)}"
            print(error_msg)
            import traceback
            traceback.print_exc()
            return error_msg, "", [], error_msg
    
    def save_report(self, markdown_content: str, json_content: str, topic: str) -> str:
        """
        Save the generated report to files.
        
        Args:
            markdown_content: Markdown report content
            json_content: JSON report content
            topic: Research topic (for filename)
        
        Returns:
            Status message with file paths
        """
        if not markdown_content or not json_content:
            return "❌ No report to save. Please generate a report first."
        
        try:
            # Create safe filename
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            safe_topic = "".join(c if c.isalnum() or c in " -_" else "_" for c in topic)
            safe_topic = "_".join(safe_topic.split())[:50]
            base_filename = f"{safe_topic}_{timestamp}"
            
            # Save files
            md_path = Config.OUTPUT_DIR / f"{base_filename}.md"
            json_path = Config.OUTPUT_DIR / f"{base_filename}.json"
            
            md_path.write_text(markdown_content, encoding="utf-8")
            json_path.write_text(json_content, encoding="utf-8")
            
            return (
                f"✅ Reports saved successfully!\n"
                f"   • Markdown: {md_path}\n"
                f"   • JSON: {json_path}"
            )
            
        except Exception as e:
            return f"❌ Error saving report: {str(e)}"
    
    def build_interface(self) -> gr.Blocks:
        """
        Build the Gradio interface.
        
        Returns:
            Gradio Blocks interface
        """
        # Custom CSS for better styling
        custom_css = """
        .gradio-container {
            font-family: 'Inter', sans-serif;
        }
        .main-header {
            text-align: center;
            margin-bottom: 2rem;
        }
        .output-box {
            border-radius: 8px;
            border: 1px solid #e5e7eb;
        }
        """
        
        with gr.Blocks(
            theme=gr.themes.Soft(),
            css=custom_css,
            title="ScholarAI Research Assistant"
        ) as interface:
            
            # Header
            gr.Markdown(
                """
                # 🎓 ScholarAI Research Assistant
                ### AI-Powered Research Synthesis
                
                Enter a research topic and let AI search, analyze, and synthesize
                comprehensive reports from web sources.
                """,
                elem_classes=["main-header"]
            )
            
            with gr.Row():
                with gr.Column(scale=1):
                    # Input section
                    gr.Markdown("## 🔍 Research Configuration")
                    
                    topic_input = gr.Textbox(
                        label="Research Topic",
                        placeholder="E.g., 'Impact of climate change on coral reefs'",
                        lines=3
                    )
                    
                    with gr.Row():
                        num_sources = gr.Slider(
                            minimum=3,
                            maximum=20,
                            value=10,
                            step=1,
                            label="Number of Sources"
                        )
                    
                    with gr.Row():
                        style_dropdown = gr.Dropdown(
                            choices=["layperson", "technical", "academic"],
                            value="layperson",
                            label="Writing Style"
                        )
                        
                        tone_dropdown = gr.Dropdown(
                            choices=["neutral", "advisory", "analytical"],
                            value="neutral",
                            label="Tone"
                        )
                    
                    research_button = gr.Button(
                        "🚀 Start Research",
                        variant="primary",
                        size="lg"
                    )
                    
                    status_output = gr.Textbox(
                        label="Status",
                        lines=4,
                        interactive=False
                    )
                
                with gr.Column(scale=2):
                    # Output section
                    gr.Markdown("## 📊 Research Results")
                    
                    with gr.Tabs():
                        with gr.Tab("📋 Summary"):
                            summary_output = gr.Markdown(
                                label="Research Report",
                                elem_classes=["output-box"]
                            )
                            
                            with gr.Row():
                                copy_tldr_btn = gr.Button("📋 Copy TL;DR", size="sm")
                                download_md_btn = gr.Button("⬇️ Download .md", size="sm")
                                download_json_btn = gr.Button("⬇️ Download .json", size="sm")
                        
                        with gr.Tab("📚 Sources"):
                            sources_table = gr.Dataframe(
                                headers=["#", "Title", "URL", "Snippet"],
                                label="Source Details",
                                wrap=True
                            )
                        
                        with gr.Tab("💾 Export Data"):
                            with gr.Tabs():
                                with gr.Tab("Markdown"):
                                    markdown_export = gr.Code(
                                        label="Markdown Format",
                                        language="markdown"
                                    )
                                
                                with gr.Tab("JSON"):
                                    json_export = gr.Code(
                                        label="JSON Format",
                                        language="json"
                                    )
            
            # Hidden state for report content
            report_state = gr.State()
            
            # Event handlers
            def run_research(*args):
                """Wrapper to handle research and update all outputs."""
                md, json_data, sources, status = self.conduct_research(*args)
                return md, json_data, sources, status, md, json_data
            
            research_button.click(
                fn=run_research,
                inputs=[
                    topic_input,
                    num_sources,
                    style_dropdown,
                    tone_dropdown
                ],
                outputs=[
                    summary_output,
                    json_export,
                    sources_table,
                    status_output,
                    markdown_export,
                    json_export
                ]
            )
            
            # Download handlers
            download_md_btn.click(
                fn=lambda md, topic: (
                    Config.OUTPUT_DIR / f"{topic.replace(' ', '_')}_{datetime.now().strftime('%Y%m%d')}.md"
                ).write_text(md) or str(Config.OUTPUT_DIR / f"{topic.replace(' ', '_')}_{datetime.now().strftime('%Y%m%d')}.md"),
                inputs=[markdown_export, topic_input],
                outputs=status_output
            )
            
            # Example queries
            gr.Markdown("## 💡 Example Research Topics")
            gr.Examples(
                examples=[
                    ["Impact of microplastics on marine ecosystems", 10, "layperson", "neutral"],
                    ["CRISPR gene editing applications in medicine", 8, "academic", "analytical"],
                    ["Quantum computing advancements in 2024", 7, "technical", "neutral"],
                    ["Effects of remote work on employee productivity", 10, "layperson", "advisory"],
                ],
                inputs=[topic_input, num_sources, style_dropdown, tone_dropdown]
            )
            
            # Footer
            gr.Markdown(
                """
                ---
                **ScholarAI** | Built with OpenAI & Gradio | [GitHub](https://github.com/your-repo)
                
                ⚠️ **Disclaimer**: AI-generated research should be verified with primary sources.
                This tool is for research assistance and not a substitute for expert analysis.
                """
            )
        
        return interface
    
    def launch(self, **kwargs):
        """
        Launch the Gradio interface.
        
        Args:
            **kwargs: Arguments to pass to gr.Blocks.launch()
        """
        interface = self.build_interface()
        interface.launch(**kwargs)


def main():
    """Main entry point for the application."""
    # Parse command-line arguments
    parser = argparse.ArgumentParser(description="ScholarAI Research Assistant")
    parser.add_argument(
        "--provider",
        type=str,
        choices=["tavily", "serpapi"],
        help="Search provider to use (tavily or serpapi)"
    )
    parser.add_argument(
        "--share",
        action="store_true",
        help="Create a public sharing link"
    )
    parser.add_argument(
        "--port",
        type=int,
        default=7860,
        help="Port to run the server on (default: 7860)"
    )
    
    args = parser.parse_args()
    
    # Initialize and launch the app
    app = ScholarAIApp(search_provider=args.provider)
    
    # Launch with configuration
    app.launch(
        server_name="0.0.0.0",  # Allow external connections
        server_port=args.port,
        share=args.share,
        show_error=True
    )


if __name__ == "__main__":
    main()
