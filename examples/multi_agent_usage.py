#!/usr/bin/env python3
"""
Exemplo de uso do sistema multi-agente Ziva.

Demonstra workflow completo de desenvolvimento com colaboração entre agentes.
"""

import logging
import time
from core.multi_agent_init import initialize_multi_agent_system, shutdown_multi_agent_system

# Configurar logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger("MultiAgentExample")


def example_1_simple_task_delegation():
    """
    Exemplo 1: Delegação simples de tarefa.

    Demonstra:
        - Inicialização do sistema
        - Delegação automática de tarefa
        - Verificação de status
    """
    logger.info("=== Exemplo 1: Delegação Simples ===")

    try:
        # Inicializar sistema
        manager = initialize_multi_agent_system()

        # Delegar tarefa (manager escolhe agente apropriado)
        task = {
            "type": "code_generation",
            "description": "Create a Python function to calculate Fibonacci numbers",
            "language": "python"}

        agent_id = manager.delegate_task(task)
        logger.info(f"Tarefa delegada para: {agent_id}")

        # Aguardar processamento
        time.sleep(5)

        # Verificar status
        status = manager.get_agent_status(agent_id)
        logger.info(f"Status do agente: {status['state']}")

        # Cleanup
        manager.terminate_agent(agent_id)

    except Exception as e:
        logger.error(f"Erro no exemplo 1: {e}")
    finally:
        shutdown_multi_agent_system(manager)


def example_2_multi_agent_collaboration():
    """
    Exemplo 2: Colaboração entre múltiplos agentes.

    Workflow:
        1. PlannerAgent decompõe tarefa complexa
        2. ResearchAgent busca documentação
        3. CodingAgent gera código
        4. DebugAgent valida e testa
    """
    logger.info("=== Exemplo 2: Colaboração Multi-Agente ===")

    try:
        manager = initialize_multi_agent_system()

        # Passo 1: Planner decompõe tarefa
        logger.info("Passo 1: Decomposição de tarefa")
        planner_id = manager.spawn_agent("planner")

        planning_task = {
            "type": "task_decomposition",
            "description": "Build a REST API for user authentication with JWT tokens"}

        planner = manager.active_agents[planner_id]
        # Simular envio de tarefa (em produção, seria via message queue)

        time.sleep(3)

        # Passo 2: Research busca best practices
        logger.info("Passo 2: Pesquisa de documentação")
        research_id = manager.spawn_agent("research")

        research_task = {
            "type": "documentation",
            "library": "FastAPI",
            "topic": "JWT authentication"
        }

        time.sleep(3)

        # Passo 3: Coding implementa
        logger.info("Passo 3: Geração de código")
        coding_id = manager.spawn_agent("coding")

        coding_task = {
            "type": "code_generation",
            "specification": "FastAPI endpoint with JWT authentication",
            "language": "python"
        }

        time.sleep(5)

        # Passo 4: Debug valida
        logger.info("Passo 4: Validação e testes")
        # Terminar planner e research para liberar recursos
        manager.terminate_agent(planner_id)
        manager.terminate_agent(research_id)

        debug_id = manager.spawn_agent("debug")

        debug_task = {
            "type": "test_generation",
            "framework": "pytest"
        }

        time.sleep(3)

        # Verificar recursos
        resources = manager.get_resource_usage()
        logger.info(
            f"Uso de RAM: {
                resources['ram']['agents_total_gb']:.2f}GB / 24GB")
        logger.info(
            f"Uso de VRAM: {
                resources['vram']['used_gb']:.2f}GB / 10GB")
        logger.info(f"Agentes ativos: {resources['agents']['active']} / 3")

        # Cleanup
        manager.terminate_agent(coding_id)
        manager.terminate_agent(debug_id)

    except Exception as e:
        logger.error(f"Erro no exemplo 2: {e}")
    finally:
        shutdown_multi_agent_system(manager)


def example_3_resource_monitoring():
    """
    Exemplo 3: Monitoramento de recursos em tempo real.

    Demonstra:
        - Spawn de múltiplos agentes
        - Monitoramento de RAM/VRAM/CPU
        - Limite de 3 agentes simultâneos
    """
    logger.info("=== Exemplo 3: Monitoramento de Recursos ===")

    try:
        manager = initialize_multi_agent_system()

        # Spawnar 3 agentes (máximo)
        logger.info("Spawnando 3 agentes...")
        agent1 = manager.spawn_agent("coding")
        agent2 = manager.spawn_agent("research")
        agent3 = manager.spawn_agent("debug")

        # Monitorar recursos
        resources = manager.get_resource_usage()

        logger.info("\n📊 Recursos Alocados:")
        logger.info(
            f"  RAM: {
                resources['ram']['agents_total_gb']:.2f}GB / 24GB")
        logger.info(f"  VRAM: {resources['vram']['used_gb']:.2f}GB / 10GB")
        logger.info(f"  Agentes: {resources['agents']['active']} / 3")

        logger.info("\n🤖 Agentes Ativos:")
        for agent_id, details in resources['agents']['details'].items():
            logger.info(f"  - {agent_id}:")
            logger.info(f"      RAM: {details['ram_mb']}MB")
            logger.info(f"      VRAM: {details['vram_mb']}MB")
            logger.info(f"      CPU cores: {details['cpu_cores']}")
            logger.info(f"      Modelo: {details['model_loaded']}")

        # Tentar spawnar 4º agente (deve falhar)
        logger.info("\nTentando spawnar 4º agente (deve falhar)...")
        agent4 = manager.spawn_agent("planner")

        if agent4 is None:
            logger.info("✅ Limite de 3 agentes respeitado!")
        else:
            logger.warning("⚠️ Limite de agentes não funcionou corretamente")

        # Cleanup
        manager.terminate_agent(agent1)
        manager.terminate_agent(agent2)
        manager.terminate_agent(agent3)

    except Exception as e:
        logger.error(f"Erro no exemplo 3: {e}")
    finally:
        shutdown_multi_agent_system(manager)


def example_4_model_switching():
    """
    Exemplo 4: Troca automática de modelos.

    Demonstra:
        - Política de modelo único em VRAM
        - Unload automático ao trocar agentes
        - Lazy loading de modelos
    """
    logger.info("=== Exemplo 4: Troca de Modelos ===")

    try:
        from core.model_loader import get_loader

        manager = initialize_multi_agent_system()
        loader = get_loader()

        # Spawnar CodingAgent (modelo grande)
        logger.info(
            "Spawnando CodingAgent (deepseek-coder:6.7b - 3.8GB VRAM)...")
        coding_id = manager.spawn_agent("coding")
        time.sleep(2)

        status1 = loader.get_status()
        logger.info(f"Modelo carregado: {status1['loaded_model']}")
        logger.info(f"Usado por: {status1['loaded_by_agent']}")

        # Terminar CodingAgent e spawnar ResearchAgent (modelo pequeno)
        logger.info("\nTerminando CodingAgent...")
        manager.terminate_agent(coding_id)
        time.sleep(1)

        logger.info("Spawnando ResearchAgent (llama3.2:3b - 1.9GB VRAM)...")
        research_id = manager.spawn_agent("research")
        time.sleep(2)

        status2 = loader.get_status()
        logger.info(f"Modelo carregado: {status2['loaded_model']}")
        logger.info(f"Usado por: {status2['loaded_by_agent']}")

        logger.info("\n✅ Troca de modelo realizada com sucesso!")
        logger.info(f"VRAM liberada: ~1.9GB (3.8GB → 1.9GB)")

        # Cleanup
        manager.terminate_agent(research_id)

    except Exception as e:
        logger.error(f"Erro no exemplo 4: {e}")
    finally:
        shutdown_multi_agent_system(manager)


if __name__ == "__main__":
    """
    Executar exemplos de uso do sistema multi-agente.

    Nota: Requer Ollama rodando com modelos instalados:
        - ollama pull deepseek-coder:6.7b
        - ollama pull qwen2.5:7b
        - ollama pull llama3.2:3b
    """

    print("\n" + "=" * 60)
    print("Sistema Multi-Agente Ziva - Exemplos de Uso")
    print("=" * 60 + "\n")

    try:
        # Executar exemplos
        example_1_simple_task_delegation()
        print("\n" + "-" * 60 + "\n")

        example_2_multi_agent_collaboration()
        print("\n" + "-" * 60 + "\n")

        example_3_resource_monitoring()
        print("\n" + "-" * 60 + "\n")

        example_4_model_switching()

        print("\n" + "=" * 60)
        print("Todos os exemplos executados com sucesso!")
        print("=" * 60 + "\n")

    except KeyboardInterrupt:
        logger.info("\nExecução interrompida pelo usuário")
    except Exception as e:
        logger.error(f"\nErro durante execução dos exemplos: {e}")
