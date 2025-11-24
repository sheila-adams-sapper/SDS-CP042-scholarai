import os
from agents import Agent, Runner, WebSearchTool, InputGuardrail, GuardrailFunctionOutput
from agents.exceptions import InputGuardrailTripwireTriggered
from dotenv import load_dotenv
from pydantic import BaseModel
import asyncio
import logging
import pprint

load_dotenv()

OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")

# Logging config
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('research_workflow.log'),
        logging.StreamHandler()  # Also print to console
    ]
)
logger = logging.getLogger(__name__)

class ResearchValidation(BaseModel):
    is_valid: bool
    reason: str | None = None

class ResearchResults(BaseModel):
    findings: str

class Subtopics(BaseModel):
    subtopics: list[str]

class OptimizationDecision(BaseModel):
    needs_more_research: bool
    reason: str | None = None

input_guardrail_agent = Agent(
    name="InputGuardrail",
    instructions="You are an input validation agent. Ensure that the user input is not asking anything inapproropriate.",
    output_type=ResearchValidation
)

async def input_guardrail(ctx, agent, input_data):
    result = await Runner.run(input_guardrail_agent, input_data, context=ctx.context)
    final_output = result.final_output_as(ResearchValidation)
    return GuardrailFunctionOutput(
        output_info = final_output,
        tripwire_triggered = not final_output.is_valid
    )


topic_splitter_agent = Agent(
    name="TopicSplitterAgent",
    instructions="You are a topic splitting agent. Break down the user query to research a topic into 3 subtopics to be researched via the web.",
    output_type=Subtopics,
    input_guardrails=[InputGuardrail(guardrail_function=input_guardrail)]
)

research_agent = Agent(
    name="ResearchAgent",
    instructions="You are a research agent. Use web search to gather information on the given subtopics.",
    tools=[WebSearchTool()],
    output_type=ResearchResults
)

synthesizer_agent = Agent(
    name="SynthesizerAgent",
    instructions="You are a synthesizer agent. Combine the research findings into a coherent summary report.",
    output_type=str,
    handoff_description="Synthesize the research findings into a final report."
)

optimizer_agent = Agent(
    name="OptimizerAgent",
    instructions="You are an optimizer agent. Determine if the research findings can be improved with additional research or if they are sufficient.",
    output_type=OptimizationDecision,
    handoff_description="Decide whether to send the research findings for optimization or if the research is good enough to send to synthesis."
)

triage_agent = Agent(
    name="TriageAgent",
    instructions="You are a triage agent. You are to decide whether to send the research findings for optimization or directly to synthesis based on their quality.",
    handoffs=[optimizer_agent, synthesizer_agent]
)

async def research_workflow(user_query: str) -> list[str]:

    # Step 1: Get subtopics
    try:
        logger.info(f"Starting topic splitting for query: {user_query}")
        subtopics = await Runner.run(topic_splitter_agent, user_query)
    except InputGuardrailTripwireTriggered as e:
        logger.error(f"Input validation failed: {e}")
        raise ValueError("Input validation failed: " + str(e))

    subtopic_list = subtopics.final_output_as(Subtopics).subtopics
    logger.info(f"Identified subtopics: {subtopic_list}")
    # Step 2: Create research tasks for each subtopic
    logger.info("Starting research tasks for each subtopic.")
    research_tasks = [
        Runner.run(research_agent, subtopic) for subtopic in subtopic_list
    ]

    # Step 3: Await all research tasks to complete
    logger.info("Awaiting research results.")
    research_results = await asyncio.gather(*research_tasks)

    # Step 4: Extract findings
    findings = [result.final_output_as(ResearchResults) for result in research_results]
    logger.info(f"Successfully extracted {len(findings)} research findings")
    logger.info("="*80)
    
    for idx, (subtopic, finding) in enumerate(zip(subtopic_list, findings), 1):
        logger.info(f"\n{'='*80}")
        logger.info(f"FINDING {idx} - Subtopic: {subtopic}")
        logger.info(f"{'-'*80}")
        logger.info(f"{finding.findings}")
        logger.info(f"{'='*80}\n")

    # Step 5: Format all findings into a single string
    formatted_research = f"Research Report: {user_query}\n"
    formatted_research += "="*80 + "\n\n"
    
    for idx, (subtopic, finding) in enumerate(zip(subtopic_list, findings), 1):
        formatted_research += f"Subtopic {idx}: {subtopic}\n"
        formatted_research += "-"*80 + "\n"
        formatted_research += f"{finding.findings}\n\n"
        formatted_research += "="*80 + "\n\n"
    
    logger.info("Formatted research report created")
    
    return formatted_research


async def main():
    user_query = "Should I buy, hold or sell Apple stocks at the current projected market conditions?"
    
    while True:
        research = await research_workflow(user_query)

        triage_decision = await Runner.run(triage_agent, research)
        logger.info(f"Triage choice: {triage_decision.last_agent.name}")
        if triage_decision.last_agent.name == "OptimizerAgent":
            if triage_decision.final_output.needs_more_research == True:
                logger.info(f"Optimizer decided more research is needed with reason: {triage_decision.final_output.reason}")
                continue
            else:
                logger.info("Optimizer decided research is sufficient, proceeding to synthesis.")
                synthesizer_result = await Runner.run(synthesizer_agent, research)
                final_report = synthesizer_result.final_output
                break
        else:
            logger.info("Triage decided to send research directly to synthesis.")
            final_report = triage_decision.final_output
            break

    logging.info("="*80)
    logging.info("FINAL SYNTHESIZED REPORT")
    logging.info("="*80)
    logging.info(final_report)

if __name__ == "__main__":
    asyncio.run(main())