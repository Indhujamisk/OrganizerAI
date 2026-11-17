import os, time, requests
from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    database_url: str = "sqlite:///./organizer.db"
    gemini_api_key: str = ""
    gemini_model: str = "gemini-2.5-flash"
    ollama_url: str = "http://localhost:11434"
    ollama_model: str = "llama3.2"
    default_provider: str = "gemini"   # gemini | ollama
    embed_model: str = "BAAI/bge-small-en-v1.5"
    chroma_dir: str = "./chroma_store"
    cors_origins: str = "http://localhost:3000"
    usd_inr: float = 84.0
    class Config:
        env_file = ".env"

settings = Settings()
TELEMETRY: list[dict] = []   # in-memory call log for /eval

def llm(prompt: str, provider: str | None = None, system: str = "") -> str:
    """Model router. Falls back to a deterministic stub if no provider is reachable."""
    provider = provider or settings.default_provider
    t0 = time.time(); text = ""
    try:
        if provider == "gemini" and settings.gemini_api_key:
            from google import genai
            c = genai.Client(api_key=settings.gemini_api_key)
            r = c.models.generate_content(model=settings.gemini_model, contents=f"{system}\n\n{prompt}")
            text = r.text or ""
        elif provider == "ollama":
            r = requests.post(f"{settings.ollama_url}/api/generate", timeout=120,
                json={"model": settings.ollama_model, "prompt": f"{system}\n\n{prompt}", "stream": False})
            text = r.json().get("response", "")
    except Exception as e:
        text = ""
    ms = (time.time() - t0) * 1000
    toks = (len(prompt) + len(text)) // 4
    cost_usd = toks / 1e6 * (0.30 if provider == "gemini" else 0.0)
    TELEMETRY.append({"provider": provider, "latency_ms": round(ms), "tokens": toks,
                      "cost_usd": round(cost_usd, 6), "cost_inr": round(cost_usd * settings.usd_inr, 4), "ts": time.time()})
    return text or "[offline-stub] No LLM reachable; using template output."
