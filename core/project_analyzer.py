"""
Project Analyzer - Ferramenta de análise de projetos remotos via P2P
Atua como consultor técnico automático
"""
import logging
from typing import Dict
from datetime import datetime
from core.p2p_learning import GabrielleConnector
from core.llm import LLMService

logger = logging.getLogger("ProjectAnalyzer")


class ProjectAnalyzer:
    """
    Analisa projetos remotos via RPC queries estruturadas
    """

    QUESTIONS = {
        "overview": """
        Descreva seu projeto:
        1. Nome e propósito
        2. Stack tecnológica principal
        3. Infraestrutura
        4. Tamanho aproximado
        """,

        "architecture": """
        Descreva sua arquitetura:
        1. Padrão arquitetural
        2. Banco de dados
        3. APIs
        4. Autenticação e segurança
        """,

        "development": """
        Sobre desenvolvimento e qualidade:
        1. Cobertura de testes (%)
        2. CI/CD pipeline
        3. Ferramentas de lint/quality
        4. Documentação
        """,

        "challenges": """
        Desafios e objetivos:
        1. Principais problemas técnicos atuais
        2. Performance bottlenecks
        3. Áreas que precisam de refatoração
        4. Features planejadas
        """,

        "collaboration": """
        Sobre colaboração:
        1. Conhecimento que você pode compartilhar
        2. Áreas onde você precisa de ajuda ou consultoria
        3. Interesse em integração com outros projetos
        """
    }

    def __init__(self, peer_host: str, peer_port: int = 9000):
        self.peer_host = peer_host
        self.peer_port = peer_port
        self.llm = LLMService()
        self.responses = {}

    def analyze(self, depth: str = "quick") -> Dict:
        """
        Executa análise do projeto remoto
        """
        logger.info(f"🔬 Iniciando análise {depth} de {self.peer_host}")

        conn = GabrielleConnector(host=self.peer_host, port=self.peer_port)
        if not conn.is_connected:
            logger.error("❌ Peer inacessível")
            return {"error": "Peer offline"}

        questions_to_ask = self._get_questions_for_depth(depth)

        for category, question in questions_to_ask.items():
            logger.info(f"   → {category}")
            response = conn.ask_remote_llm(question)
            self.responses[category] = response

        analysis = self._synthesize_analysis()

        return {
            "peer": self.peer_host,
            "timestamp": datetime.now().isoformat(),
            "depth": depth,
            "raw_responses": self.responses,
            "analysis": analysis
        }

    def _get_questions_for_depth(self, depth: str) -> Dict:
        """Retorna subset de perguntas baseado na profundidade"""
        if depth == "quick":
            return {k: v for k, v in self.QUESTIONS.items() if k in [
                "overview", "architecture"]}
        elif depth == "health":
            return {k: v for k, v in self.QUESTIONS.items() if k !=
                    "collaboration"}
        else:
            return self.QUESTIONS

    def _synthesize_analysis(self) -> Dict:
        """Usa LLM local para sintetizar análise"""
        prompt = f"""
        Analise as seguintes informações sobre um projeto de software remoto:

        {self._format_responses()}

        Forneça uma análise estruturada JSON com:
        {{
            "tech_stack": ["lista de tecnologias"],
            "architecture_pattern": "padrão",
            "strengths": ["pontos fortes"],
            "weaknesses": ["pontos fracos"],
            "recommendations": ["recomendações"],
            "collaboration_opportunities": ["oportunidades"]
        }}

        Responda APENAS o JSON, sem explicações.
        """

        response = self.llm.completion(prompt, temperature=0.3)

        try:
            import json
            return json.loads(response.strip().replace(
                "```json", "").replace("```", ""))
        except BaseException:
            return {"raw": response}

    def _format_responses(self) -> str:
        """Formata respostas para análise"""
        formatted = ""
        for category, response in self.responses.items():
            formatted += f"\n### {category.upper()}\n{response}\n"
        return formatted

    def generate_report(self, analysis: Dict, output_path: str):
        """Gera relatório markdown"""
        with open(output_path, 'w') as f:
            f.write(f"# Análise de Projeto: {analysis['peer']}\n\n")
            f.write(f"**Data:** {analysis['timestamp']}\n\n")
            f.write(f"**Profundidade:** {analysis['depth']}\n\n")
            f.write("---\n\n")
            if 'tech_stack' in analysis['analysis']:
                f.write("## 🛠️ Tech Stack\n")
                for tech in analysis['analysis']['tech_stack']:
                    f.write(f"- {tech}\n")
                f.write("\n")
            f.write("## 📊 Análise\n\n")
            if 'strengths' in analysis['analysis']:
                f.write("### ✅ Pontos Fortes\n")
                for s in analysis['analysis']['strengths']:
                    f.write(f"- {s}\n")
                f.write("\n")
            if 'weaknesses' in analysis['analysis']:
                f.write("### ⚠️ Pontos de Atenção\n")
                for w in analysis['analysis']['weaknesses']:
                    f.write(f"- {w}\n")
                f.write("\n")
            if 'recommendations' in analysis['analysis']:
                f.write("## 💡 Recomendações\n")
                for i, rec in enumerate(
                        analysis['analysis']['recommendations'], 1):
                    f.write(f"{i}. {rec}\n")
                f.write("\n")
            if 'collaboration_opportunities' in analysis['analysis']:
                f.write("## 🤝 Oportunidades de Colaboração\n")
                for opp in analysis['analysis']['collaboration_opportunities']:
                    f.write(f"- {opp}\n")
        logger.info(f"✅ Relatório salvo: {output_path}")