import sys
from pathlib import Path
from typing import Literal

from pydantic import ValidationError
from pydantic_ai import Agent
from pydantic_ai.common_tools.duckduckgo import duckduckgo_search_tool

from agents.configuration import ModelSettings

from .configuration import settings
from .output_models import AuthorInfo

_prompts_folder = Path(__file__).parent / "prompts"
_author_info_prompt = _prompts_folder.joinpath("author_info.txt").read_text(encoding="utf-8")
_book_description_prompt = _prompts_folder.joinpath("book_description.txt").read_text(encoding="utf-8")
try:
    _model_settings: ModelSettings = settings
    print("✅ Model configuration loaded successfully:")
    print(f"   Provider: {_model_settings.provider}")
    print(f"   Model Name: {_model_settings.model_name}")
    if _model_settings.base_url:
        print(f"   Base URL: {_model_settings.base_url}")
except ValidationError as e:
    print("\n❌ CRITICAL: Configuration Error!")
    print(e)  # This will print exactly which field is missing or invalid
    sys.exit(1) # Stop the app gracefully instead of a massive traceback
_ai_model = _model_settings.get_pydantic_ai_model()

def get_agent(agent_type: Literal["author_info", "book_description", "health"]) -> Agent:
    match agent_type:
        case "author_info":
            return Agent(
                model=_ai_model,
                system_prompt=_author_info_prompt,
                tools=[duckduckgo_search_tool()],
                output_type=AuthorInfo,
            )
        case "book_description":
            return Agent(
                model=_ai_model,
                system_prompt=_book_description_prompt,
                tools=[duckduckgo_search_tool()],
                output_type=str,
            )
        case "health":
            return Agent(
                model=_ai_model,
                system_prompt="""Please tell me that everything is ok like you were Bill Cosby""",
                output_type=str,
            )
        case _:
            raise ValueError(f"Unknown agent type: {agent_type}")