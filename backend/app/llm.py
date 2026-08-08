from langchain_groq import ChatGroq
from backend.app.config import GROQ_API_KEY

def get_groq_llm():
    return ChatGroq(
        groq_api_key=GROQ_API_KEY,
        model_name="openai/gpt-oss-20b",
        temperature=0.1,
        max_tokens=1024
    )