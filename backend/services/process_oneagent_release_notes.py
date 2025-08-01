# OneAgent release notes processing service for Dynatrace documentation

# --------------------------------------------------------------
# Import dependencies for OneAgent processing
# --------------------------------------------------------------

import logging
import openai
from fastapi.responses import JSONResponse
from .data_models import ComponentLatestReleaseVersion, ComponentLatestReleaseSummary
from .prompts.oneagent_prompts import get_oneagent_summary_prompt, get_oneagent_version_prompt

# --------------------------------------------------------------
# Configure logging for OneAgent service
# --------------------------------------------------------------

logger = logging.getLogger(__name__)

# --------------------------------------------------------------
# Define OneAgent service class for release notes processing
# --------------------------------------------------------------


class ProcessOneAgentReleaseNotes:
    """Service class for processing OneAgent release notes and version information"""
    
    def __init__(self, openai_client: openai.OpenAI):
        """Initialize with OpenAI client"""
        self.openai_client = openai_client

    # --------------------------------------------------------------
    # Main processing methods
    # --------------------------------------------------------------

    async def process_dynatrace_release_news(self):
        """Main method to process Dynatrace release news"""
        logger.info("Received request for Dynatrace release news")
        
        one_agent_latest_version = await self._get_oneagent_latest_version()
        if "error" in one_agent_latest_version:
            return JSONResponse(status_code=500, content=one_agent_latest_version)

        summary_result = await self._get_oneagent_release_summary(one_agent_latest_version)
        if "error" in summary_result:
            return JSONResponse(status_code=500, content=summary_result)
        
        return summary_result

    # --------------------------------------------------------------
    # Version retrieval methods
    # --------------------------------------------------------------

    async def _get_oneagent_latest_version(self):
        """Get the latest OneAgent version"""
        return await self._oneagent_latest_version()

    async def _oneagent_latest_version(self) -> ComponentLatestReleaseVersion:
        """Fetch the latest OneAgent version from OpenAI"""
        if not self.openai_client:
            return {"error": "OpenAI API key not configured."}
        
        try:
            oneagent_version_prompt = get_oneagent_version_prompt()
            print(f"Sending prompt to OpenAI: {oneagent_version_prompt}")

            oneagent_version_response = self.openai_client.responses.parse(
                model="gpt-4o",  # Use gpt-4o instead of gpt-4.1
                input=oneagent_version_prompt,
                tools=[{"type": "web_search_preview"}],
                text_format=ComponentLatestReleaseVersion
            )
            result = oneagent_version_response.output_parsed
            if result is None:
                return {"error": "Failed to extract the latest OneAgent version."}
            
            print(f"Received response from OpenAI: {result}")
            return result.version
            
        except Exception as e:
            return {"error": str(e)}

    # --------------------------------------------------------------
    # Release summary methods
    # --------------------------------------------------------------

    async def _get_oneagent_release_summary(self, version: str):
        """Get the summary for a given OneAgent version"""
        try:
            summary_prompt = get_oneagent_summary_prompt(version)
            print(f"Sending summary prompt to OpenAI: {summary_prompt}")
            
            summary_response = self.openai_client.responses.parse(
                model="gpt-4o",  # Use gpt-4o instead of gpt-4.1 for better web access
                input=summary_prompt,
                tools=[{"type": "web_search_preview"}],
                text_format=ComponentLatestReleaseSummary
            )
            result = summary_response.output_parsed
            print(f"Received summary from OpenAI: {result}")
            
            if result is None:
                return {"error": "Failed to get summary from OpenAI."}
            
            # Ensure latestVersion is set
            result.latestVersion = version
            return result
                    
        except Exception as e:
            return {"error": str(e)}
