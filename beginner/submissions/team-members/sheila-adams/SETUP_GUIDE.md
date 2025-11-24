# ScholarAI Setup & Usage Guide

Complete guide for setting up and using the ScholarAI research assistant.

## 📋 Prerequisites

- Python 3.9 or higher
- pip (Python package manager)
- OpenAI API key
- Either Tavily API key OR SerpAPI key

## 🚀 Quick Start

### 1. Clone and Setup

```bash
# Clone the repository
git clone <your-repo-url>
cd scholarai-beginner

# Create virtual environment
python -m venv venv

# Activate virtual environment
# On macOS/Linux:
source venv/bin/activate
# On Windows:
venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt
```

### 2. Configuration

```bash
# Copy the example environment file
cp .env.example .env

# Edit .env and add your API keys
# Use your preferred text editor:
nano .env
# or
vim .env
```

Your `.env` file should look like:

```env
OPENAI_API_KEY=sk-...your-key-here...
TAVILY_API_KEY=tvly-...your-key-here...
# OR
SERPAPI_API_KEY=...your-serpapi-key...

OPENAI_MODEL=gpt-4-turbo-preview
```

### 3. Get API Keys

#### OpenAI API Key (Required)
1. Visit [OpenAI Platform](https://platform.openai.com/)
2. Sign up or log in
3. Navigate to API Keys section
4. Create new key
5. Copy to `.env` file

#### Tavily API Key (Option 1 - Recommended)
1. Visit [Tavily](https://tavily.com/)
2. Sign up for free account
3. Get API key from dashboard
4. Copy to `.env` file

#### SerpAPI Key (Option 2)
1. Visit [SerpAPI](https://serpapi.com/)
2. Sign up for account
3. Get API key
4. Copy to `.env` file

## 🧪 Testing the Setup

### Test Individual Components

```bash
# Test configuration
python src/config.py

# Test search tool
python src/tools/search.py

# Test research agent
python src/agents/research.py

# Test synthesizer
python src/agents/synthesizer.py

# Test exporters
python src/exporters/export.py
```

### Quick Research Test

```python
# test_quick.py
from src.agents.research import ResearchAgent
from src.agents.synthesizer import SynthesizerAgent

# Initialize
research_agent = ResearchAgent()
synthesizer = SynthesizerAgent()

# Research
result = research_agent.research(
    topic="artificial intelligence in healthcare",
    num_results=5
)

# Synthesize
report = synthesizer.synthesize_from_research_result(result)

print(report)
```

## 🎨 Running the Application

### Launch Gradio Interface and select a search provider
#### Will default to tavily, since it is detected first in config

```bash
python app.py --provider tavily
python app.py --provider serpapi
```

The application will start at: `http://localhost:7860`

### Usage Flow

1. **Enter Research Topic**: Describe what you want to research
2. **Configure Settings**:
   - Number of sources (3-20)
   - Writing style (layperson/technical/academic)
   - Tone (neutral/advisory/analytical)
3. **Click "Start Research"**: Wait for AI to search and synthesize
4. **Review Results**:
   - Summary tab: Full formatted report
   - Sources tab: All sources used
   - Export Data tab: Raw markdown/JSON
5. **Export**: Download in markdown or JSON format

## 🐳 Docker Deployment

### Build Image

```bash
docker build -t scholarai:latest .
```

### Run Container

```bash
docker run -d \
  --name scholarai \
  -p 7860:7860 \
  --env-file .env \
  scholarai:latest
```

### Docker Compose (Optional)

```yaml
# docker-compose.yml
version: '3.8'
services:
  scholarai:
    build: .
    ports:
      - "7860:7860"
    env_file:
      - .env
    volumes:
      - ./outputs:/app/outputs
    restart: unless-stopped
```

Run with: `docker-compose up -d`

## ☁️ Deployment Options

### Hugging Face Spaces

1. Create account at [Hugging Face](https://huggingface.co/)
2. Create new Space
3. Choose Gradio SDK
4. Upload code or link GitHub repo
5. Add secrets (API keys) in Space settings
6. Deploy automatically

### Streamlit Cloud (Alternative)

If you prefer Streamlit:
1. Adapt `app.py` to Streamlit format
2. Deploy to [Streamlit Cloud](https://streamlit.io/cloud)
3. Add secrets in app settings

### Railway / Render

Both support Docker deployments:
1. Connect your GitHub repo
2. Railway/Render auto-detects Dockerfile
3. Add environment variables
4. Deploy

## 🔧 Advanced Configuration

### Custom Models

Edit `.env`:
```env
OPENAI_MODEL=gpt-4-turbo-preview  # Default
# Or use:
# OPENAI_MODEL=gpt-4
# OPENAI_MODEL=gpt-3.5-turbo-16k
```

### Search Provider Selection (currently enabled as arg when deploying app.py)

```python
# In code, explicitly choose provider:
from src.tools.search import WebSearchTool

# Force Tavily
search_tool = WebSearchTool(provider="tavily")

# Force SerpAPI
search_tool = WebSearchTool(provider="serpapi")
```

### Output Directory

Edit `src/config.py`:
```python
OUTPUT_DIR: Path = Path("outputs")  # Change as needed
```

## 📊 Project Structure Explained

```
scholarai-beginner/
│
├── src/                          # Source code
│   ├── config.py                # Configuration management
│   ├── tools/                   # Search tools
│   │   └── search.py           # Web search implementations
│   ├── agents/                  # AI agents
│   │   ├── research.py         # Research agent
│   │   └── synthesizer.py      # Synthesis agent
│   └── exporters/               # Export utilities
│       └── export.py           # Markdown/JSON exporters
│
├── app.py                        # Gradio application
├── requirements.txt              # Python dependencies
├── .env                          # Environment variables (git-ignored)
├── Dockerfile                    # Docker configuration
└── outputs/                      # Generated reports
```

## 🐛 Troubleshooting

### "OPENAI_API_KEY is required"
- Check `.env` file exists in project root
- Verify API key is valid and has credits
- Ensure no extra spaces in `.env` file

### "No search API key configured"
- Add either TAVILY_API_KEY or SERPAPI_API_KEY to `.env`
- Verify API key is valid

### "Module not found" errors
- Ensure virtual environment is activated
- Run: `pip install -r requirements.txt`
- Check Python version: `python --version` (should be 3.9+)

### Gradio won't start
- Check port 7860 isn't already in use
- Try different port: modify `app.py` server_port
- Check firewall settings

### API Rate Limits
- OpenAI: Check usage dashboard for rate limits
- Tavily: Free tier has daily limits
- Consider adding rate limiting in code if needed

## 📝 Best Practices

### For Research Topics
- Be specific and focused
- Include key terms and context
- Example good topics:
  - "Impact of microplastics on marine food chains"
  - "CRISPR applications in treating sickle cell disease"
  - "Machine learning approaches for protein folding prediction"

### For API Management
- Monitor API usage regularly
- Set up billing alerts
- Cache results when possible
- Use appropriate models (GPT-4 vs GPT-3.5)

### For Production
- Use environment-specific configs
- Implement proper logging
- Add error tracking (e.g., Sentry)
- Set up monitoring
- Implement rate limiting
- Add user authentication if needed

## 🎓 Learning Resources

### Understanding the Code

1. **Agent Architecture**: Start with `src/agents/research.py`
2. **Tool Design**: Review `src/tools/search.py`
3. **Prompt Engineering**: See synthesis prompts in `synthesizer.py`
4. **UI Development**: Study `app.py` for Gradio patterns

### Further Learning

- [OpenAI Function Calling](https://platform.openai.com/docs/guides/function-calling)
- [Gradio Documentation](https://gradio.app/docs)
- [Prompt Engineering Guide](https://www.promptingguide.ai/)
- [Agentic AI Patterns](https://www.anthropic.com/research)

---

**Happy Researching! 🎓🔬**
