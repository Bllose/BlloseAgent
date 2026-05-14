from langchain_core.prompts import ChatPromptTemplate

from src.config.settings import settings


def create_chat_chain():
    llm = settings.get_llm()
    prompt = ChatPromptTemplate.from_messages([
        ("system", "You are BlloseAgent, a helpful AI assistant."),
        ("human", "{input}"),
    ])
    return prompt | llm
