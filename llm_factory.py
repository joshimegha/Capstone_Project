import os
import json
from pathlib import Path

from dotenv import load_dotenv
from langchain_openai import ChatOpenAI
from langchain_google_genai import ChatGoogleGenerativeAI

BASE_DIR = Path(__file__).resolve().parent
load_dotenv(BASE_DIR / ".env")


def load_config() -> dict:
    with open(BASE_DIR / "config.json", "r", encoding="utf-8") as f:
        return json.load(f)


def get_llm(config: dict):
    provider = config["provider"]
    if provider == "openai":
        cfg = config["openai"]
        return ChatOpenAI(
            model=cfg["model"],
            temperature=cfg["temperature"],
            max_tokens=cfg["max_token"],
            api_key=os.getenv("OPENAI_API_KEY"),
        )
    if provider == "gemini":
        cfg = config["gemini"]
        return ChatGoogleGenerativeAI(
            model=cfg["model"],
            temperature=cfg["temperature"],
            max_tokens=cfg["max_token"],
            api_key=os.getenv("GEMINI_API_KEY"),
        )
    raise ValueError("Invalid provider in config.json [It must be openai or gemini only]")
