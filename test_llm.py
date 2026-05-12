from app.services.llm_factory import get_llm

llm = get_llm("ollama")

response = llm.generate(
    system_prompt="You are a helpful assistant",
    user_message="Who is Abdallah Yassein?"
)

print(response)