
from langchain_core.messages import HumanMessage
from langchain_ollama import ChatOllama
from langchain_core.prompts import PromptTemplate
from langchain_core.output_parsers import StrOutputParser
import datetime

# Mock Context simulating what was likely retrieved from Wikipedia
MOCK_CONTEXT = [
    """A Guerra Russo-Ucraniana é um conflito contínuo entre a Rússia e a Ucrânia que começou em fevereiro de 2014.""",
    """Em fevereiro de 2022, a Rússia lançou uma invasão em grande escala da Ucrânia.""",
    """Vários países forneceram ajuda militar à Ucrânia, incluindo Estados Unidos, Reino Unido, Polônia e outros membros da OTAN.""",
    """A Bielorrússia permitiu que tropas russas usassem seu território para a invasão.""",
    """Não há declaração formal de guerra de outros países contra a Rússia, embora muitos tenham imposto sanções."""]

QUESTION = "quantos paises estao em guerra com a russia"


def test_generate():
    llm = ChatOllama(model="llama3.1:8b", temperature=0)
    current_time = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    # NEW PROMPT (reproducing the change in core/agent/nodes.py)
    template = """You are a helpful AI assistant. Answer the user's question directly and concisely.

        System Information:
        Current Date/Time: {current_time}

        Rules:
        1. Base your answer PRIMARILY on the Context.
        2. If the Context contains relevant facts, synthesize them to answer the user's question directly.
        3. If the Context is partial, answer based on what IS available and mention what is missing, but DO NOT REFUSE to answer.
        4. If the Context mentions a conflict (e.g. "Russo-Ukrainian War"), and the user asks "who is at war", INFER the answer from the participants mentioned.
        5. Keep your answer concise, professional and helpful.
        6. Answer in Portuguese (pt-BR).

        Question: {question}

        Context:
        {documents}

        Answer:"""

    prompt = PromptTemplate(
        template=template,
        input_variables=["question", "documents", "current_time"],
    )

    chain = prompt | llm | StrOutputParser()

    print("--- TESTING GENERATION (NEW PROMPT) ---")
    response = chain.invoke({
        "documents": MOCK_CONTEXT,
        "question": QUESTION,
        "current_time": current_time
    })

    print("\nResponse:")
    print(response)

    # Test new refusal logic
    refusals = [
        "i don't know",
        "não sei",
        "não tenho informações",
        "no information",
        "cannot answer",
        "não há informações",
        "a resposta não está disponível",
        "não encontrei informações",
        "desculpe",
        "sinto muito"]
    is_refusal = any(r in response.lower() for r in refusals)
    print(f"\nIs Refusal (Updated Logic): {is_refusal}")


if __name__ == "__main__":
    test_generate()
