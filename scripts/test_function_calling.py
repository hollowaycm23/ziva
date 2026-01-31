
from langchain_core.messages import HumanMessage
from core.graph.ziva_graph import app
import os
import sys

# Add project root to path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))


def test_fc():
    print("🚀 Iniciando Teste de Function Calling Nativo...")

    # Query que exige ferramenta mas NÃO usa keywords exatas se possível,
    # ou usa keywords mas queremos ver o Tool Call, não o Regex.
    query = "Quanto custa 100 dólares em reais hoje?"

    print(f"❓ Query: {query}\n")

    inputs = {"input": query, "messages": []}

    try:
        final_state = app.invoke(inputs)

        print("\n✅ Execução Concluída!")
        print("-" * 50)

        # Verificar se houve tool calls
        messages = final_state.get("messages", [])
        tool_calls_count = 0
        tool_outputs = []

        for msg in messages:
            if hasattr(msg, "tool_calls") and msg.tool_calls:
                tool_calls_count += len(msg.tool_calls)
                print(f"🛠️ Tool Call Detectado: {msg.tool_calls}")

            if msg.type == "tool":
                tool_outputs.append(msg.content)
                print(f"📤 Tool Output: {msg.content[:100]}...")

        if tool_calls_count > 0:
            print(
                f"\n🎉 SUCESSO! {tool_calls_count} chamadas de ferramenta nativas realizadas.")
        else:
            print("\n⚠️ FALHA: Nenhuma chamada de ferramenta detectada.")

        print("-" * 50)
        print(f"🤖 Resposta Final: {final_state.get('response')}")

    except Exception as e:
        print(f"❌ Erro na execução: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    test_fc()
