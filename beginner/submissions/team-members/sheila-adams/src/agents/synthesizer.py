"""
Synthesizer Agent for creating structured research reports.

This agent takes curated sources and synthesizes them into a comprehensive,
well-structured research report with proper citations and analysis.
"""

from typing import List, Dict, Optional, Literal
from dataclasses import dataclass, asdict
from openai import OpenAI
import json
import sys
sys.path.append('/home/claude/scholarai-beginner')

from src.config import Config


@dataclass
class ResearchReport:
    """
    Structured research report output.
    
    This dataclass defines the structure of the final research report,
    ensuring consistency and making it easy to export to different formats.
    """
    topic: str
    tldr: str  # ≤120 words
    key_findings: List[Dict[str, str]]  # Each has 'finding' and 'citation'
    conflicts_and_caveats: str
    top_sources: List[Dict[str, str]]  # Top 5 with 'title', 'url', 'why_matters'
    synthesis_date: str
    
    def to_dict(self) -> Dict:
        """Convert to dictionary for serialization."""
        return asdict(self)
    
    def __str__(self) -> str:
        """Human-readable string representation."""
        output = []
        output.append(f"Topic: {self.topic}")
        output.append(f"\nTL;DR:\n{self.tldr}")
        output.append(f"\n\nKey Findings ({len(self.key_findings)}):")
        for i, finding in enumerate(self.key_findings, 1):
            output.append(f"{i}. {finding['finding']}")
            output.append(f"   Citation: {finding['citation']}")
        output.append(f"\n\nConflicts & Caveats:\n{self.conflicts_and_caveats}")
        output.append(f"\n\nTop Sources:")
        for i, source in enumerate(self.top_sources, 1):
            output.append(f"{i}. {source['title']}")
            output.append(f"   URL: {source['url']}")
            output.append(f"   Why it matters: {source['why_matters']}")
        return "\n".join(output)


class SynthesizerAgent:
    """
    Synthesizer Agent that creates structured research reports.
    
    This agent takes research sources and synthesizes them into a
    comprehensive report with:
    - Executive summary (TL;DR)
    - Key findings with citations
    - Conflicts and caveats
    - Curated source list with analysis
    
    The agent uses structured output to ensure consistent formatting.
    """
    
    def __init__(
        self,
        model: str = Config.SYNTHESIS_MODEL
    ):
        """
        Initialize the Synthesizer Agent.
        
        Args:
            model: OpenAI model to use
        """
        self.client = OpenAI(api_key=Config.OPENAI_API_KEY)
        self.model = model
        print(f"✓ SynthesizerAgent initialized with model: {self.model}")
    
    def _build_synthesis_prompt(
        self,
        topic: str,
        sources: List[Dict],
        style: str,
        tone: str
    ) -> str:
        """
        Build the synthesis prompt with sources and requirements.
        
        Args:
            topic: Research topic
            sources: List of source dictionaries
            style: Writing style (technical, layperson, academic)
            tone: Tone (neutral, advisory, analytical)
        
        Returns:
            Formatted prompt string
        """
        # Format sources for the prompt
        sources_text = []
        for i, source in enumerate(sources, 1):
            sources_text.append(
                f"[{i}] {source.get('title', 'Untitled')}\n"
                f"    URL: {source.get('url', 'N/A')}\n"
                f"    Content: {source.get('snippet', 'No content available')}\n"
            )
        
        sources_formatted = "\n".join(sources_text)
        
        # Style-specific instructions
        style_instructions = {
            "technical": (
                "Use technical terminology and assume domain expertise. "
                "Include specific methodologies, data, and technical details."
            ),
            "layperson": (
                "Use accessible language that a general audience can understand. "
                "Explain technical terms and avoid jargon."
            ),
            "academic": (
                "Use formal academic language with appropriate terminology. "
                "Focus on research methodology, evidence quality, and scholarly discourse."
            )
        }
        
        # Tone-specific instructions
        tone_instructions = {
            "neutral": "Present information objectively without advocacy.",
            "advisory": "Provide guidance and recommendations based on the evidence.",
            "analytical": "Critically analyze the evidence and highlight implications."
        }
        
        prompt = f"""You are synthesizing research on: {topic}

SOURCES PROVIDED:
{sources_formatted}

TASK: Create a comprehensive research report with the following structure:

1. TL;DR (≤120 words)
   - Concise summary of the main findings
   - Answer the core research question directly

2. Key Findings (3-7 findings)
   - Each finding should be substantive and specific
   - MUST include a citation in format: [Source #]
   - Focus on the most important and well-supported points

3. Conflicts & Caveats
   - Note any disagreements between sources
   - Identify limitations or gaps in the research
   - Highlight areas needing more investigation

4. Top 5 Sources
   - Rank the most valuable sources
   - For each, explain WHY it matters (specific contribution)

STYLE: {style_instructions.get(style, style_instructions['layperson'])}
TONE: {tone_instructions.get(tone, tone_instructions['neutral'])}

IMPORTANT:
- Base ALL findings on the provided sources
- ALWAYS cite with [Source #] notation
- Be specific - avoid generic statements
- Acknowledge uncertainty where appropriate
- If sources conflict, note this explicitly

Please provide your synthesis in the following JSON format:
{{
    "tldr": "Your TL;DR here (≤120 words)",
    "key_findings": [
        {{
            "finding": "First key finding with details",
            "citation": "[1], [3]"
        }}
    ],
    "conflicts_and_caveats": "Discussion of conflicts, limitations, and caveats",
    "top_sources": [
        {{
            "title": "Source title",
            "url": "Source URL",
            "why_matters": "Specific reason why this source is valuable"
        }}
    ]
}}
"""
        return prompt
    
    def synthesize(
        self,
        topic: str,
        sources: List[Dict],
        style: Literal["technical", "layperson", "academic"] = "layperson",
        tone: Literal["neutral", "advisory", "analytical"] = "neutral"
    ) -> ResearchReport:
        """
        Synthesize sources into a structured research report.
        
        Args:
            topic: Research topic/question
            sources: List of source dictionaries from research agent
            style: Writing style for the report
            tone: Tone of the report
        
        Returns:
            ResearchReport object
        """
        print(f"\n{'='*60}")
        print(f"📝 Synthesizer Agent: Creating report on '{topic}'")
        print(f"   Style: {style} | Tone: {tone}")
        print(f"   Sources: {len(sources)}")
        print(f"{'='*60}\n")
        
        if not sources:
            raise ValueError("No sources provided for synthesis")
        
        # Build the synthesis prompt
        prompt = self._build_synthesis_prompt(topic, sources, style, tone)
        
        # Call OpenAI with response format specification
        print("🤖 Generating synthesis...")
        
        try:
            response = self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {
                        "role": "system",
                        "content": (
                            "You are an expert research synthesizer. "
                            "Create comprehensive, well-cited research reports. "
                            "Always output valid JSON matching the requested structure."
                        )
                    },
                    {
                        "role": "user",
                        "content": prompt
                    }
                ],
                response_format={"type": "json_object"},  # Ensure JSON output
                temperature=0.7  # Balance creativity and consistency
            )
            
            # Parse the JSON response
            content = response.choices[0].message.content
            synthesis_data = json.loads(content)
            
            print("✓ Synthesis complete!")
            
            # Validate and enhance the response
            if "top_sources" not in synthesis_data or not synthesis_data["top_sources"]:
                # Generate top sources from input if not provided
                synthesis_data["top_sources"] = [
                    {
                        "title": s.get("title", "Untitled"),
                        "url": s.get("url", ""),
                        "why_matters": "Key source for this research"
                    }
                    for s in sources[:5]
                ]
            
            # Create ResearchReport object
            from datetime import datetime
            report = ResearchReport(
                topic=topic,
                tldr=synthesis_data.get("tldr", ""),
                key_findings=synthesis_data.get("key_findings", []),
                conflicts_and_caveats=synthesis_data.get("conflicts_and_caveats", ""),
                top_sources=synthesis_data.get("top_sources", [])[:5],  # Ensure only 5
                synthesis_date=datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            )
            
            # Validate TL;DR length
            tldr_word_count = len(report.tldr.split())
            if tldr_word_count > 120:
                print(f"⚠️  Warning: TL;DR is {tldr_word_count} words (target: ≤120)")
            
            print(f"   TL;DR: {tldr_word_count} words")
            print(f"   Key findings: {len(report.key_findings)}")
            print(f"   Top sources: {len(report.top_sources)}")
            
            return report
            
        except json.JSONDecodeError as e:
            print(f"❌ Error: Failed to parse JSON response: {e}")
            print(f"Response content: {content}")
            raise
        except Exception as e:
            print(f"❌ Error during synthesis: {e}")
            raise
    
    def synthesize_from_research_result(
        self,
        research_result: Dict,
        style: str = "layperson",
        tone: str = "neutral"
    ) -> ResearchReport:
        """
        Convenience method to synthesize directly from research agent output.
        
        Args:
            research_result: Output from ResearchAgent.research()
            style: Writing style
            tone: Report tone
        
        Returns:
            ResearchReport object
        """
        return self.synthesize(
            topic=research_result["query"],
            sources=research_result["sources"],
            style=style,
            tone=tone
        )


if __name__ == "__main__":
    # Test the Synthesizer Agent
    print("Testing SynthesizerAgent...")
    
    # Mock sources for testing
    mock_sources = [
        {
            "title": "CRISPR-Cas9: A Revolutionary Gene Editing Tool",
            "url": "https://example.com/crispr1",
            "snippet": "CRISPR-Cas9 has transformed genetic engineering by enabling precise DNA modifications. Studies show 95% accuracy in targeting specific genes."
        },
        {
            "title": "Clinical Applications of CRISPR Technology",
            "url": "https://example.com/crispr2",
            "snippet": "CRISPR is being used in clinical trials for sickle cell disease, with promising early results showing symptom reduction in 80% of patients."
        },
        {
            "title": "Ethical Concerns in Gene Editing",
            "url": "https://example.com/ethics",
            "snippet": "The scientific community debates the ethical implications of germline editing, particularly regarding unintended consequences and equity of access."
        }
    ]
    
    try:
        agent = SynthesizerAgent()
        
        report = agent.synthesize(
            topic="CRISPR gene editing applications in medicine",
            sources=mock_sources,
            style="layperson",
            tone="neutral"
        )
        
        print("\n" + "="*60)
        print("SYNTHESIS REPORT")
        print("="*60)
        print(report)
        
    except Exception as e:
        print(f"Error: {e}")
        import traceback
        traceback.print_exc()
