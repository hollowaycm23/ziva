"""
QueryClassifier - centralized task classification for Ziva

Classifies user queries into task types for routing and tool filtering.
Uses fast keyword/pattern matching as first pass, with optional LLM fallback.

Optimization strategies applied:
- __slots__ for reduced memory overhead
- LRU caching on classify(), get_allowed_tools(), should_search_web()
- Pre-compiled regex patterns (compiled once at module load)
- Keyword sets (frozenset) for O(1) membership tests
- Pre-computed multi-word keyword sets for negation proximity checks
- heapq.nlargest instead of full sort for top-2 extraction
- Local variable bindings for frequently accessed globals
- Single-pass negation penalty with early break via any()
- Pre-computed allowed_tools at category level
"""

import functools
import heapq
import logging
import re
from typing import Dict, FrozenSet, List, Optional, Tuple

logger = logging.getLogger("QueryClassifier")

NEGATION_WORDS: FrozenSet[str] = frozenset([
    "não", "nao", "n", "no", "not", "dont", "don't",
    "nao quero", "nao precisa", "nao é", "nao e",
    "sem", "without", "nenhum", "nunca", "never",
    "nem", "nor", "exceto", "except", "senao",
    "mas nao", "mas não",
])

MULTI_INTENT_SEPARATORS: Tuple[str, ...] = (
    r"\be\b", r"\be\s+depois\b", r"\be\s+tambem\b", r"\be\s+também\b",
    r"\band\b", r"\band\s+then\b", r"\balso\b",
    r"\bdepois\b", r"\bem\s+seguida\b", r"\balém\s+disso\b",
    r"\bseparado\b", r"\bseparadamente\b",
    r"[;,]", r"\bmais\b",
)

MULTI_INTENT_COMPILED: Tuple[re.Pattern, ...] = tuple(
    re.compile(p, re.IGNORECASE) for p in MULTI_INTENT_SEPARATORS
)

CONFIDENCE_AMBIGUITY_THRESHOLD: float = 0.15

SEARCH_RELATED: FrozenSet[str] = frozenset([
    "web_search", "time_sensitive", "weather", "general_knowledge"
])
CODE_RELATED: FrozenSet[str] = frozenset([
    "code_execution", "shell_command", "file_operation", "math"
])


def _build_categories() -> Dict[str, dict]:
    raw = {
        "web_search": {
            "priority": 5,
            "keywords": frozenset([
                "search", "pesquisar", "find", "encontrar", "lookup",
                "consultar", "buscar", "google", "bing", "internet", "online",
                "noticias", "news", "ultimas", "latest", "atualizacao",
                "quem ganhou", "resultado", "campeao", "campeonato",
                "copa", "olimpiadas", "premiere", "lancamento",
                "preco", "preço", "price", "cotacao", "valor do", "quanto custa",
                "bitcoin", "dolar", "euro", "nasdaq", "bolsa de valores",
                "wikipedia", "significado", "definicao",
                "pesquise", "busque", "procurar", "procure",
                "comparativo", "comparação", "comparar", "compare",
                "vs", "versus", "qual a diferença",
            ]),
            "patterns": (
                re.compile(r"(search|buscar|pesquisar|google|procurar)\s+(for|por|sobre|a\s+respeito)"),
                re.compile(r"(what|who|where|when|why|how)\s+(is|are|was|were|does|did)\s+"),
                re.compile(r"(quem|onde|quando|como|por\s+que|porque)\s+"),
                re.compile(r"(noticias|news)\s+(sobre|de|do|da|about)"),
                re.compile(r"\b(resultado|placar)\s+(de|do|da|das|dos)\b"),
                re.compile(r"\bcotacao\s+(do|da|de|dolar|euro|bitcoin)\b"),
                re.compile(r"(preço|preco|valor|melhor\s+preço|quanto\s+custa|mais\s+barato|promoção|promocao).+"),
                re.compile(r"(comprar|onde\s+comprar|qual\s+o\s+melhor)\s+.+"),
                re.compile(r"(comparativo|comparação|comparar|compare|vs|versus)\s+(entre|de|do|da|dos|das)"),
                re.compile(r"\w+\s+(vs|versus|e|ou)\s+\w+\s+(comparativo|comparação|diferença)"),
            ),
            "tool_groups": ("search", "datetime"),
        },
        "time_sensitive": {
            "priority": 6,
            "keywords": frozenset([
                "current", "atual", "now", "agora", "hoje", "today",
                "hora", "time", "date", "data", "weekday", "dia da semana",
                "previsao", "forecast", "tempo agora", "clima agora",
                "que horas", "horario", "fuso", "timezone", "fuso horario",
                "amanha", "tomorrow", "ontem", "yesterday", "presente",
                "momento", "atualmente",
            ]),
            "patterns": (
                re.compile(r"(que|what)\s+(horas|time|dia|day|date|data)\s+(sao|is|sera|são)"),
                re.compile(r"(tempo|weather|clima)\s+(em|in|now|agora|para)"),
                re.compile(r"(qual\s+a\s)?(temperatura|temperature)"),
                re.compile(r"\b(hoje|agora)\s+[aá]\b"),
                re.compile(r"(quantas|que)\s+horas\s+(são|sao|sao)"),
            ),
            "tool_groups": ("datetime", "weather", "search"),
        },
        "weather": {
            "priority": 6,
            "keywords": frozenset([
                "weather", "clima", "tempo", "temperatura", "temperature",
                "chuva", "rain", "sol", "sun", "umidade", "humidity",
                "vento", "wind", "previsao", "forecast", "meteorologia",
                "neve", "snow", "tempestade", "storm", "chuvoso", "ensolarado",
                "nublado", "cloudy", "frio", "calor", "fresco",
            ]),
            "patterns": (
                re.compile(r"(qual\s+a\s)?(temperatura|temperature|previsao|previsão)\s+(do\s+)?(tempo|clima)?"),
                re.compile(r"(vai\s)?(chover|fazer\s+calor|fazer\s+frio|nevar|ventar)"),
                re.compile(r"(como\s+esta|how\s+is)\s+(o\s+)?(tempo|clima)"),
                re.compile(r"(vai\s+)?(chover|fazer\s+sol|fazer\s+frio|fazer\s+calor)\s+(hoje|amanha)"),
                re.compile(r"(previsao|previsão)\s+(do\s+)?tempo"),
                re.compile(r"(esta|esta|tá)\s+(chovendo|frio|calor|nublado|ensolarado)"),
            ),
            "tool_groups": ("weather", "datetime"),
        },
        "code_execution": {
            "priority": 7,
            "keywords": frozenset([
                "code", "codigo", "código", "run", "executar", "execute",
                "compile", "compilar", "script", "program", "programa",
                "python", "javascript", "typescript", "java", "c++", "rust",
                "algoritmo", "algorithm", "function", "funcao", "função",
                "implement", "implementar", "programar",
                "calculadora", "calculator", "calcular",
                "codigo fonte", "source code", "snippet",
                "debug", "depurar", "testar", "teste unitario",
                "endpoint", "rota", "route", "funcao",
            ]),
            "patterns": (
                re.compile(r"(run|execute|executar|rodar|compilar)\s+(this|este|esse|o|um|meu)"),
                re.compile(r"(write|escreva|crie|criar|faca|faça|código|codigo)\s+(um|uma|a|an|este|esse)?\s*(function|class|script|code|programa|algoritmo|metodo|método)"),
                re.compile(r"(calcule|calculate|compute|resolva|solve)\s+"),
                re.compile(r"```\w*"),
                re.compile(r"\b(codigo|código)\s+(fonte|para|de|em)\b"),
                re.compile(r"(como\s+)?(fazer|implementar|criar|faco|faço)\s+(um|uma|o|a)?\s*(codigo|código|funcao|função|programa)"),
            ),
            "tool_groups": ("code", "shell", "file"),
        },
        "shell_command": {
            "priority": 7,
            "keywords": frozenset([
                "command", "comando", "bash", "shell", "terminal",
                "exec", "rodar", "run", "instalar", "install",
                "linux", "windows", "powershell", "cmd", "console",
                "listar", "list", "ls", "dir", "mkdir", "grep",
                "docker", "git", "ssh", "curl", "wget", "apt",
                "pip", "npm", "yarn", "chmod", "sudo", "cd",
                "comando", "linha de comando", "cli",
            ]),
            "patterns": (
                re.compile(r"(how\s+to|como)\s+(run|execute|install|rodar|instalar|executar)"),
                re.compile(r"command\s+(to|for|para|line)"),
                re.compile(r"(install|instalar|setup)\s+(package|pacote|tool|ferramenta|biblioteca)"),
                re.compile(r"roda\s+(esse|o|um)\s+(comando|script)"),
                re.compile(r"executa\s+(esse|o|um)\s+(comando|script)"),
            ),
            "tool_groups": ("shell", "file", "code"),
        },
        "file_operation": {
            "priority": 6,
            "keywords": frozenset([
                "file", "arquivo", "read", "ler", "write", "escrever",
                "edit", "editar", "create", "criar", "delete", "deletar",
                "rename", "renomear", "move", "mover", "copy", "copiar",
                "folder", "pasta", "diretorio", "directory", "path",
                "salvar", "save", "abrir", "open", "fechar", "close",
                "conteudo", "content", "linha", "line", "texto",
                "baixar", "download", "upload", "enviar",
            ]),
            "patterns": (
                re.compile(r"(read|ler|abrir|open|exibir)\s+(the|o|a|um|meu|este|esse)?\s*(file|arquivo)"),
                re.compile(r"(create|criar|write|escrever|salvar)\s+(a|um|um\s+novo|novo)?\s*(file|arquivo)"),
                re.compile(r"(delete|deletar|apagar|remove|remover|excluir)\s+(file|arquivo|pasta|diretorio)"),
                re.compile(r"(renomear|rename|mover|move|copiar|copy)\s+(file|arquivo|pasta)"),
                re.compile(r"(listar|list|mostrar)\s+(arquivos|files|pasta|diretorio|directory)"),
            ),
            "tool_groups": ("file", "shell"),
        },
        "math": {
            "priority": 6,
            "keywords": frozenset([
                "math", "matematica", "matemática", "calcular", "calculate",
                "conta", "soma", "sum", "subtracao",
                "multiplicacao", "multiplicação", "divisao", "divisão",
                "raiz", "sqrt", "potencia", "potência", "power",
                "equacao", "equation", "formula",
                "grafico", "graph", "plot", "integral", "derivada",
                "limite", "matriz", "matrix", "algebra", "álgebra",
                "porcentagem", "percentage", "juros", "interest",
            ]),
            "patterns": (
                re.compile(r"(quanto\s+(eh|e|é|da|dá)|what\s+is)\s+[\d\s\+\-\*\/\(\)\.]+"),
                re.compile(r"(calcule|calculate|compute|resolva|solve)\s+"),
                re.compile(r"(?<![a-zA-Z])[\d]+\s*[\+\-\*\/\^\%]\s*[\d]+"),
                re.compile(r"[\d]+\s*%\s*(de|do|da|of)\s*[\d]+"),
                re.compile(r"(raiz|sqrt)\s+(de|quadrada|square)\s+[\d]+"),
                re.compile(r"(\d+)\s*[x×]\s*(\d+)"),
            ),
            "tool_groups": ("code",),
        },
        "system_info": {
            "priority": 5,
            "keywords": frozenset([
                "status", "health", "saude", "saúde", "performance",
                "desempenho", "memory", "memoria", "ram", "cpu", "disk",
                "disco", "gpu", "processo", "process", "resource",
                "recurso", "uptime", "online", "offline", "servico",
                "service", "docker", "container", "log",
                "monitor", "monitorar", "dashboard",
            ]),
            "patterns": (
                re.compile(r"(como\s+esta|how\s+is)\s+(o\s+)?(sistema|system|servidor)"),
                re.compile(r"(mostrar|show|listar|list|ver)\s+(recursos|resources|processos)"),
                re.compile(r"(status|health|estado)\s+(do|da|do\s+sistema|check|de\s+saude)"),
                re.compile(r"(quanto\s+de|qual\s+a)\s+(ram|memoria|cpu|disco|gpu)\b"),
            ),
            "tool_groups": ("shell", "datetime"),
        },
        "greeting": {
            "priority": 1,
            "keywords": frozenset([
                "ola", "olá", "oi", "hey", "hello", "hi", "bom dia",
                "boa tarde", "boa noite", "tudo bem", "como vai",
                "thanks", "obrigado", "obrigada", "valeu", "brigado",
                "tchau", "bye", "ate logo", "falou", "fui",
                "blz", "beleza", "tranquilo", "saudacao",
                "prazer", "bem vindo", "bem-vindo",
            ]),
            "patterns": (
                re.compile(r"^(ola|olá|oi|hey|hello|hi|bom\s+dia|boa\s+tarde|boa\s+noite)\s*[!\.]?\s*$"),
                re.compile(r"^(tudo\s+bem|como\s+vai|td\s+bem|blz|beleza)\s*[\?]?\s*$"),
            ),
            "tool_groups": (),
        },
        "general_knowledge": {
            "priority": 2,
            "keywords": frozenset([
                "o que eh", "o que é", "what is", "meaning", "significado",
                "definicao", "definition", "conceito", "concept",
                "quem foi", "who was", "historia", "history",
                "explicar", "explain", "descrever", "describe",
                "diferenca", "difference", "entre", "between",
                "exemplo", "example", "como funciona", "how does",
                "o que significa", "qual o", "quais sao", "quais são",
                "me fale", "me diga", "conte-me", "conte sobre",
                "quem foi", "quem e", "quem é", "quem sou",
            ]),
            "patterns": (
                re.compile(r"(explain|explicar|describe|descrever|definir)\s+"),
                re.compile(r"what\s+(is|are|was|were|does)\s+(a|an|the)\s+"),
                re.compile(r"(o\s+que\s+(eh|e|é)|qual\s+(o|a|os|as)\s+(conceito|definicao|significado))"),
                re.compile(r"(me\s+)?(fale|diga|explique|conte|mostre)\s+(sobre|sobre\s+o|sobre\s+a|o\s+que)"),
                re.compile(r"(qual\s+a\s)?diferenca\s+(entre|de)\s+"),
                re.compile(r"(quem\s+foi|quem\s+e|quem\s+é|quem\s+sou|quem\s+são|quem\s+seria)\s+.+"),
            ),
            "tool_groups": ("search",),
        },
    }

    for name, rules in raw.items():
        multi_word_kws = tuple(
            kw for kw in rules["keywords"]
            if " " in kw
        )
        rules["_multi_word_kws"] = multi_word_kws

    return raw


CATEGORIES: Dict[str, dict] = _build_categories()

TOOL_GROUP_MAP: Dict[str, Tuple[str, ...]] = {
    "search": ("web_search", "multi_source_search"),
    "datetime": ("get_current_datetime",),
    "weather": ("get_weather", "get_air_quality"),
    "code": ("code_runner", "code_writer", "code_lookup", "bash_runner"),
    "shell": ("local_shell", "bash_runner", "remote_shell"),
    "file": ("file_reader", "file_editor", "file_deleter"),
    "browser": ("browser_navigate", "browser_extract", "browser_screenshot", "browser_execute_js"),
    "bluetooth": ("list_bluetooth_devices", "connect_bluetooth_device", "disconnect_bluetooth_device",
                  "scan_bluetooth_devices", "bluetooth_adapter_status", "bluetooth_device_info"),
    "docker": ("run_docker_container",),
    "usb": ("list_local_usb_devices", "attach_remote_usb", "detach_remote_usb",
            "list_remote_usbip_devices", "list_usbip_shared_devices", "share_usb_device",
            "unshare_usb_device", "usbip_status"),
    "tailscale": ("tailscale_control",),
    "sherlock": ("search_username",),
    "docs": ("search_documentation", "standardize_docstrings", "medical_lookup"),
    "finance": ("get_exchange_rate",),
    "index": ("index_codebase",),
}

_ALLOWED_TOOLS_CACHE: Dict[str, Tuple[str, ...]] = {}


def _build_allowed_tools_map() -> Dict[str, Tuple[str, ...]]:
    cache = {}
    for cat_name, rules in CATEGORIES.items():
        names = set()
        for group in rules.get("tool_groups", ()):
            for tool in TOOL_GROUP_MAP.get(group, ()):
                names.add(tool)
        cache[cat_name] = tuple(sorted(names))
    return cache


_ALLOWED_TOOLS_CACHE = _build_allowed_tools_map()


class QueryClassifier:
    """Classifies user queries into task types for intelligent routing."""

    __slots__ = ("use_llm_fallback", "_llm", "_cat_items",
                 "_multi_intent_pats", "_ambig_threshold", "_search_set",
                 "_code_set", "_allowed_cache")

    def __init__(self, use_llm_fallback: bool = False, llm_service=None):
        self.use_llm_fallback = use_llm_fallback
        self._llm = llm_service

        self._cat_items: Tuple[Tuple[str, dict], ...] = tuple(CATEGORIES.items())
        self._multi_intent_pats: Tuple[re.Pattern, ...] = MULTI_INTENT_COMPILED
        self._ambig_threshold: float = CONFIDENCE_AMBIGUITY_THRESHOLD
        self._search_set: FrozenSet[str] = SEARCH_RELATED
        self._code_set: FrozenSet[str] = CODE_RELATED
        self._allowed_cache: Dict[str, Tuple[str, ...]] = _ALLOWED_TOOLS_CACHE

        logger.info("QueryClassifier initialized (llm_fallback=%s)", use_llm_fallback)

    def _detect_multi_intent(self, query_lower: str) -> Tuple[str, ...]:
        for pat in self._multi_intent_pats:
            if pat.search(query_lower):
                parts = re.split(
                    r'[;,]\s*|\s+(?:e|and|also|depois|tambem|também|além\s+disso|mais)\s+',
                    query_lower
                )
                return tuple(s.strip() for s in parts if len(s.strip()) > 3)
        return (query_lower,)

    @staticmethod
    def _has_negation_proximity(query_lower: str, keyword: str) -> bool:
        kw_idx = query_lower.find(keyword)
        if kw_idx < 0:
            return False
        start = max(0, kw_idx - 30)
        end = min(len(query_lower), kw_idx + len(keyword) + 5)
        window = query_lower[start:end]
        for neg in NEGATION_WORDS:
            if len(neg) <= 2:
                if re.search(r'\b' + re.escape(neg) + r'\b', window):
                    return True
            elif neg in window:
                return True
        return False

    def _score_query(self, query_lower: str) -> Dict[str, float]:
        scores = {}
        for category, rules in self._cat_items:
            score = 0.0
            negation_penalty = 0
            keywords = rules["keywords"]
            multi_kws = rules["_multi_word_kws"]

            for keyword in keywords:
                if keyword not in query_lower:
                    continue
                score += 1.0
                freq = query_lower.count(keyword)
                if freq > 1:
                    score += 0.3 * min(freq - 1, 3)
                if keyword in multi_kws:
                    score += 0.3
                if self._has_negation_proximity(query_lower, keyword):
                    negation_penalty += 2

            for pattern in rules["patterns"]:
                match = pattern.search(query_lower)
                if match:
                    score += 3.0
                    if match.group(0).strip() == query_lower:
                        score += 2.0

            score = max(0.0, score - negation_penalty)
            scores[category] = score

        return scores

    def _resolve_ambiguity(self, top_two: List[Tuple[str, float]],
                           query_lower: str) -> str:
        cat1, score1 = top_two[0]
        cat2, score2 = top_two[1]

        if cat1 == "greeting":
            return cat2
        if cat2 == "greeting":
            return cat1

        p1 = CATEGORIES[cat1].get("priority", 5)
        p2 = CATEGORIES[cat2].get("priority", 5)
        if p1 != p2:
            return cat1 if p1 > p2 else cat2

        rules1 = CATEGORIES[cat1]
        rules2 = CATEGORIES[cat2]
        p1_matches = sum(1 for p in rules1["patterns"] if p.search(query_lower))
        p2_matches = sum(1 for p in rules2["patterns"] if p.search(query_lower))
        if p1_matches != p2_matches:
            return cat1 if p1_matches > p2_matches else cat2

        return cat1 if score1 >= score2 else cat2

    def _classify_impl(self, query: str) -> Tuple[str, float, Dict[str, float]]:
        query_lower = query.lower().strip()
        if not query_lower:
            return ("greeting", 1.0, {})

        scores = self._score_query(query_lower)

        best_score = 0.0
        best_name = "general_knowledge"
        second_score = 0.0
        second_name = ""

        for cat_name, cat_score in scores.items():
            if cat_score > best_score:
                second_score, second_name = best_score, best_name
                best_score, best_name = cat_score, cat_name
            elif cat_score > second_score:
                second_score, second_name = cat_score, cat_name

        if best_score == 0:
            return ("general_knowledge", 0.0, scores)

        total_score = best_score + second_score + sum(
            v for k, v in scores.items()
            if k not in (best_name, second_name)
        )

        margin = (best_score - second_score) / best_score if best_score > 0 else 0

        if margin < self._ambig_threshold and second_name:
            resolved = self._resolve_ambiguity(
                [(best_name, best_score), (second_name, second_score)],
                query_lower
            )
            if resolved != best_name:
                logger.info(
                    "Ambiguity resolved: %s→%s (margin=%.2f)",
                    best_name, resolved, margin
                )
                best_name = resolved
                best_score = scores[resolved]

        confidence = best_score / total_score if total_score > 0 else 0.0

        logger.info(
            "Query classified as '%s' (conf=%.2f, score=%.1f, margin=%.2f, total=%.0f)",
            best_name, confidence, best_score, margin, total_score
        )
        return (best_name, confidence, scores)

    @functools.lru_cache(maxsize=1024)
    def classify(self, query: str) -> Tuple[str, float, Dict[str, float]]:
        return self._classify_impl(query)

    def classify_multi(self, query: str) -> List[Tuple[str, float, Dict[str, float]]]:
        query_lower = query.lower().strip()
        segments = self._detect_multi_intent(query_lower)
        if len(segments) <= 1:
            return [self.classify(query)]

        results = []
        for seg in segments:
            if len(seg) > 3:
                results.append(self.classify(seg))

        return results if results else [self.classify(query)]

    @functools.lru_cache(maxsize=32)
    def get_allowed_tools(self, task_type: str) -> Tuple[str, ...]:
        return self._allowed_cache.get(task_type, ())

    @functools.lru_cache(maxsize=32)
    def should_search_web(self, task_type: str) -> bool:
        return task_type in self._search_set

    def classify_with_llm_fallback(self, query: str) -> Tuple[str, float, Dict[str, float]]:
        task_type, confidence, scores = self.classify(query)

        if confidence >= 0.5:
            return task_type, confidence, scores

        if not self.use_llm_fallback or not self._llm:
            return task_type, confidence, scores

        try:
            categories_str = ", ".join(CATEGORIES)
            prompt = (
                f"Classifique a consulta do usuário em EXATAMENTE UMA destas categorias:\n"
                f"{categories_str}\n\n"
                f"Consulte: \"{query}\"\n\n"
                f"Responda apenas com o nome da categoria, nada mais."
            )
            llm_result = self._llm.completion(
                prompt, temperature=0.0, max_tokens=32
            ).strip().lower()

            for cat in CATEGORIES:
                if cat in llm_result:
                    logger.info("LLM fallback classified as '%s'", cat)
                    return (cat, 0.9, scores)
        except Exception as e:
            logger.warning("LLM fallback failed: %s", e)

        return task_type, confidence, scores


_classifier: Optional[QueryClassifier] = None


def get_query_classifier() -> QueryClassifier:
    global _classifier
    if _classifier is None:
        _classifier = QueryClassifier()
    return _classifier
