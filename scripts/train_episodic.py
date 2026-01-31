#!/usr/bin/env python3
import sys
import os
import logging
import time

# Setup Path
sys.path.append(os.getcwd())

from core.episodic_memory import EpisodicMemory

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("EpisodicTrainer")

EXERCISES = [
    # --- SISTEMA ZIVA (10) ---
    {"q": "Quem criou o sistema Ziva?", "a": "O sistema Ziva foi arquitetado como um agente autônomo avançado, desenvolvido para auxiliar em tarefas de codificação, pesquisa e orquestração de sistemas."},
    {"q": "Qual é a porta da API do Ziva?", "a": "A API do Ziva roda por padrão na porta 8000."},
    {"q": "O que é o Qdrant no contexto do Ziva?", "a": "O Qdrant é o banco de dados vetorial utilizado pelo Ziva para armazenar memória semântica e episódica de longo prazo."},
    {"q": "Para que serve o script start.sh?", "a": "O script start.sh é o orquestrador unificado que inicia todos os serviços do ecossistema Ziva, incluindo Docker e processos Python."},
    {"q": "Qual a função do Kiwix no Ziva?", "a": "O Kiwix provê acesso offline a conhecimentos enciclopédicos (como Wikipedia), permitindo que o Ziva responda perguntas mesmo sem internet."},
    {"q": "O que é o SearXNG?", "a": "SearXNG é uma meta-engine de busca focada em privacidade, usada pelo Ziva para realizar pesquisas na web sem rastreamento."},
    {"q": "Onde ficam os logs do sistema?", "a": "Os logs do sistema Ziva são armazenados no diretório 'logs/', incluindo arquivos como ziva_system.log e api_server.log."},
    {"q": "Qual a linguagem principal do Ziva?", "a": "O núcleo do Ziva é escrito principalmente em Python, utilizando bibliotecas como LangChain, FastAPI e Qdrant Client."},
    {"q": "O que é o EpisodicMemory?", "a": "EpisodicMemory é o módulo responsável por armazenar experiências passadas (pares de pergunta-resposta) para permitir que o Ziva aprenda com suas próprias interações."},
    {"q": "Como verificar o status dos serviços?", "a": "O status dos serviços pode ser verificado executando o script './status.sh' na raiz do projeto."},

    # --- PYTHON / CODING (20) ---
    {"q": "Como declarar uma função em Python?", "a": "Em Python, utiliza-se a palavra-chave 'def' seguida do nome da função e parênteses. Exemplo: def minha_funcao(): pass"},
    {"q": "O que é uma list comprehension?", "a": "List comprehension é uma forma concisa de criar listas em Python. Exemplo: [x**2 for x in range(10)]."},
    {"q": "Qual a diferença entre tupla e lista?", "a": "Listas são mutáveis (podem ser alteradas), enquanto tuplas são imutáveis (seus valores são fixos após a criação)."},
    {"q": "O que faz o método .join()?", "a": "O método .join() concatena elementos de um iterável (como uma lista de strings) em uma única string, usando um separador especificado."},
    {"q": "Como instalar pacotes em Python?", "a": "Geralmente utiliza-se o gerenciador de pacotes 'pip'. Exemplo: pip install requests."},
    {"q": "O que é o GIL em Python?", "a": "GIL (Global Interpreter Lock) é um mecanismo que impede que múltiplas threads nativas executem bytecodes Python simultaneamente, limitando o paralelismo em CPU-bound."},
    {"q": "O que é um decorator?", "a": "Um decorator é uma função que envolve outra função para estender ou modificar seu comportamento sem alterar seu código fonte, usando a sintaxe @decorator."},
    {"q": "Como tratar exceções em Python?", "a": "Utiliza-se os blocos try, except, else e finally para capturar e tratar erros durante a execução."},
    {"q": "O que é self em uma classe?", "a": "O 'self' é uma convenção para referenciar a instância atual da classe dentro de seus métodos."},
    {"q": "Como ler um arquivo texto em Python?", "a": "Usa-se a função open() com o modo 'r', preferencialmente em um bloco 'with'. Exemplo: with open('file.txt', 'r') as f: content = f.read()"},
    {"q": "O que é PEP 8?", "a": "PEP 8 é o guia de estilo oficial para código Python, definindo convenções de formatação e boas práticas."},
    {"q": "Como verificar o tipo de uma variável?", "a": "Utiliza-se a função type() ou isinstance(). Exemplo: type(x) ou isinstance(x, int)."},
    {"q": "O que é um ambiente virtual (venv)?", "a": "Um ambiente virtual isola as dependências de um projeto Python, evitando conflitos de versão entre diferentes projetos."},
    {"q": "Como fazer um request HTTP GET?", "a": "Com a biblioteca requests: requests.get('url'). Na biblioteca padrão: urllib.request.urlopen('url')."},
    {"q": "O que é um gerador (generator)?", "a": "Um gerador é uma função que retorna um iterador usando 'yield', produzindo valores sob demanda e economizando memória."},
    {"q": "Qual a diferença entre '==' e 'is'?", "a": "'==' verifica igualdade de valor, enquanto 'is' verifica identidade de objeto (se ocupam o mesmo espaço na memória)."},
    {"q": "Como converter string para inteiro?", "a": "Utiliza-se a função int(). Exemplo: int('123')."},
    {"q": "O que é o __init__?", "a": "É o método construtor de uma classe em Python, chamado automaticamente ao criar uma nova instância."},
    {"q": "Como importar um módulo?", "a": "Usa-se a palavra-chave 'import'. Exemplo: import math."},
    {"q": "O que é indentação significativa?", "a": "Em Python, a indentação define os blocos de código (escopo), ao contrário de chaves {} usadas em C ou Java."},

    # --- CIÊNCIA E FÍSICA (20) ---
    {"q": "Qual a velocidade da luz?", "a": "A velocidade da luz no vácuo é de aproximadamente 299.792.458 metros por segundo."},
    {"q": "O que diz a Primeira Lei de Newton?", "a": "Também chamada de Lei da Inércia, diz que um corpo em repouso tende a permanecer em repouso, e um em movimento tende a permanecer em movimento, a menos que uma força atue sobre ele."},
    {"q": "Qual é a fórmula da relatividade restrita?", "a": "A equação mais famosa é E=mc², que relaciona energia (E), massa (m) e a velocidade da luz ao quadrado (c²)."},
    {"q": "O que é um átomo?", "a": "Átomo é a unidade básica da matéria, composto por um núcleo (prótons e nêutrons) e uma eletrosfera (elétrons)."},
    {"q": "Qual o planeta mais próximo do Sol?", "a": "Mercúrio é o planeta mais próximo do Sol no nosso sistema solar."},
    {"q": "O que é fotossíntese?", "a": "É o processo pelo qual plantas e outros organismos convertem energia luminosa em energia química, produzindo glicose e oxigênio."},
    {"q": "Qual a temperatura de congelamento da água?", "a": "A água congela a 0 graus Celsius (32 graus Fahrenheit) ao nível do mar."},
    {"q": "O que é gravidade?", "a": "Gravidade é a força de atração fundamental que age entre todas as massas no universo."},
    {"q": "Quem propôs a teoria da evolução?", "a": "Charles Darwin (e independentemente Alfred Russel Wallace) propôs a teoria da evolução pela seleção natural."},
    {"q": "O que é o DNA?", "a": "O DNA (Ácido Desoxirribonucleico) carrega a informação genética usada no desenvolvimento, funcionamento e reprodução dos organismos vivos."},
    {"q": "O que é um buraco negro?", "a": "É uma região do espaço-tempo com gravidade tão intensa que nada, nem mesmo a luz, pode escapar dela."},
    {"q": "Qual o elemento químico mais abundante no universo?", "a": "O Hidrogênio é o elemento mais abundante, constituindo cerca de 75% da massa bariônica do universo."},
    {"q": "O que é entropia?", "a": "Entropia é uma medida de desordem ou aleatoriedade em um sistema termodinâmico."},
    {"q": "Qual a idade aproximada da Terra?", "a": "A Terra tem aproximadamente 4,54 bilhões de anos."},
    {"q": "O que são placas tectônicas?", "a": "São grandes blocos da litosfera terrestre que se movem, causando terremotos e formação de montanhas."},
    {"q": "Qual a função das mitocôndrias?", "a": "Mitocôndrias são as organelas responsáveis pela respiração celular e produção de energia (ATP)."},
    {"q": "O que é a Tabela Periódica?", "a": "É uma disposição tabular dos elementos químicos, ordenados por número atômico, configurações eletrônicas e propriedades químicas recorrentes."},
    {"q": "O que é o Big Bang?", "a": "É a teoria cosmológica predominante para a origem do universo, descrevendo sua expansão a partir de um estado de densidade e temperatura extremas."},
    {"q": "O que é fusão nuclear?", "a": "É o processo onde dois núcleos atômicos leves se unem para formar um mais pesado, liberando grande quantidade de energia (como no Sol)."},
    {"q": "Qual a unidade de medida de força?", "a": "No Sistema Internacional, a unidade de força é o Newton (N)."},

    # --- HISTÓRIA E GEOGRAFIA (20) ---
    {"q": "Quem foi o primeiro homem na Lua?", "a": "Neil Armstrong foi o primeiro humano a pisar na Lua, em 1969, na missão Apollo 11."},
    {"q": "Qual a capital do Brasil?", "a": "Brasília é a capital federal do Brasil."},
    {"q": "Quando ocorreu a Segunda Guerra Mundial?", "a": "A Segunda Guerra Mundial ocorreu entre 1939 e 1945."},
    {"q": "Quem descobriu o Brasil?", "a": "A chegada dos portugueses ao Brasil é atribuída à expedição de Pedro Álvares Cabral em 1500."},
    {"q": "Qual é o maior país do mundo em área?", "a": "A Rússia é o maior país do mundo em extensão territorial."},
    {"q": "Onde fica a Torre Eiffel?", "a": "A Torre Eiffel fica em Paris, na França."},
    {"q": "Quem foi Napoleão Bonaparte?", "a": "Foi um líder militar e político francês que se destacou durante a Revolução Francesa e construiu um grande império no início do século XIX."},
    {"q": "Qual é o rio mais longo do mundo?", "a": "O Rio Nilo e o Rio Amazonas disputam o título, mas medições recentes frequentemente colocam o Amazonas como o mais longo."},
    {"q": "O que foi a Revolução Industrial?", "a": "Foi o período de transição para novos processos de manufatura na Europa e EUA, entre 1760 e 1840."},
    {"q": "Qual a moeda do Japão?", "a": "A moeda do Japão é o Iene (JPY)."},
    {"q": "Quantos continentes existem?", "a": "Geralmente considera-se 7 continentes: África, Antártida, Ásia, Europa, América do Norte, América do Sul e Oceania (ou 6 dependendo do modelo geográfico)."},
    {"q": "Quem pintou a Mona Lisa?", "a": "Leonardo da Vinci, durante o Renascimento."},
    {"q": "Qual a capital da Alemanha?", "a": "Berlim é a capital da Alemanha."},
    {"q": "O que foi o Império Romano?", "a": "O período pós-republicano da antiga civilização romana, caracterizado por governo autocrático e vastas possessões territoriais."},
    {"q": "Quem foi Nelson Mandela?", "a": "Foi um líder anti-apartheid e o primeiro presidente negro da África do Sul."},
    {"q": "Onde fica Machu Picchu?", "a": "Fica no Peru, sendo uma antiga cidade Inca nos Andes."},
    {"q": "Qual oceano banha o Brasil?", "a": "O Oceano Atlântico."},
    {"q": "Quando caiu o Muro de Berlim?", "a": "O Muro de Berlim caiu em 1989, simbolizando o fim da Guerra Fria."},
    {"q": "Quem foi Cleópatra?", "a": "Foi a última governante ativa do Reino Ptolemaico do Egito."},
    {"q": "Qual a montanha mais alta do mundo?", "a": "O Monte Everest é a montanha mais alta em relação ao nível do mar."},

    # --- LÓGICA E MATEMÁTICA (10) ---
    {"q": "Quanto é 2 + 2?", "a": "2 + 2 é igual a 4."},
    {"q": "O que é um número primo?", "a": "Um número primo é um número natural maior que 1 que tem apenas dois divisores: 1 e ele mesmo."},
    {"q": "Qual a raiz quadrada de 64?", "a": "A raiz quadrada de 64 é 8."},
    {"q": "O que é Pi?", "a": "Pi (π) é a razão entre a circunferência de um círculo e seu diâmetro, aproximadamente 3.14159."},
    {"q": "Quanto é 10% de 200?", "a": "10% de 200 é 20."},
    {"q": "O que é um algoritmo?", "a": "Um algoritmo é uma sequência finita de instruções bem definidas para resolver um problema ou realizar uma tarefa."},
    {"q": "Qual o próximo número na sequência 1, 1, 2, 3, 5?", "a": "O próximo é 8 (Sequência de Fibonacci: 3 + 5)."},
    {"q": "O que é um teorema?", "a": "Teorema é uma afirmação que pode ser provada como verdadeira através de outras verdades já estabelecidas (axiomas)."},
    {"q": "Quanto é 7 vezes 8?", "a": "7 vezes 8 é 56."},
    {"q": "O que é média aritmética?", "a": "É a soma de um conjunto de números dividida pela quantidade de números nesse conjunto."},

    # --- CULTURA POP E LITERATURA (20) ---
    {"q": "Quem escreveu Harry Potter?", "a": "J.K. Rowling."},
    {"q": "Quem é o Batman?", "a": "Bruce Wayne, um super-herói bilionário da DC Comics que combate o crime em Gotham City."},
    {"q": "O que é a Força em Star Wars?", "a": "É um campo de energia metafísico criado por todos os seres vivos que conecta a galáxia."},
    {"q": "Quem escreveu Dom Casmurro?", "a": "Machado de Assis."},
    {"q": "Qual banda canta 'Hey Jude'?", "a": "The Beatles."},
    {"q": "Quem é o Homem de Ferro?", "a": "Tony Stark, um gênio bilionário da Marvel que constrói uma armadura de alta tecnologia."},
    {"q": "O que significa '42' no Guia do Mochileiro das Galáxias?", "a": "É a 'Resposta para a Grande Pergunta sobre a Vida, o Universo e Tudo Mais'."},
    {"q": "Quem escreveu O Senhor dos Anéis?", "a": "J.R.R. Tolkien."},
    {"q": "Qual o nome do criador do Facebook?", "a": "Mark Zuckerberg."},
    {"q": "Quem é o Mario?", "a": "O encanador mascote da Nintendo, protagonista da franquia de jogos Super Mario."},
    {"q": "Qual série tem dragões e o Trono de Ferro?", "a": "Game of Thrones (baseada nas Crônicas de Gelo e Fogo)."},
    {"q": "Quem escreveu Romeu e Julieta?", "a": "William Shakespeare."},
    {"q": "O que é a Matrix no filme?", "a": "Uma realidade simulada criada por máquinas sencientes para subjugar a população humana."},
    {"q": "Quem é o Pokémon mascote da franquia?", "a": "Pikachu."},
    {"q": "Qual o nome do navio do Titanic?", "a": "RMS Titanic."},
    {"q": "Quem canta 'Thriller'?", "a": "Michael Jackson."},
    {"q": "Qual o herói amigo do Capitão América?", "a": "Bucky Barnes (Soldado Invernal) ou Sam Wilson (Falcão), entre outros."},
    {"q": "Quem escreveu 'A Divina Comédia'?", "a": "Dante Alighieri."},
    {"q": "O que é um Hobbit?", "a": "Uma raça fictícia de pessoas pequenas com pés peludos criada por Tolkien."},
    {"q": "Qual o filme de maior bilheteria da história (até 2024)?", "a": "Avatar (disputa com Vingadores: Ultimato dependendo de relançamentos)."}
]

def train():
    print(f"🚀 Iniciando treinamento de Memória Episódica com {len(EXERCISES)} exercícios...")
    
    memory = EpisodicMemory()
    success_count = 0
    start_time = time.time()
    
    for i, ex in enumerate(EXERCISES):
        query = ex["q"]
        answer = ex["a"]
        
        # Artificial delay to prevent flooding logs too fast if needed, but upsert is fast
        result = memory.remember(query, answer, source="training_script_v1")
        
        if result:
            success_count += 1
            status = "✅"
        else:
            status = "❌"
            
        # Progress bar simple
        sys.stdout.write(f"\rProcessando {i+1}/{len(EXERCISES)} {status}")
        sys.stdout.flush()

    total_time = time.time() - start_time
    print(f"\n\n🏁 Treinamento concluído em {total_time:.2f}s")
    print(f"   Sucessos: {success_count}/{len(EXERCISES)}")
    print(f"   Memórias agora residem na coleção '{memory.collection}' no Qdrant.")

if __name__ == "__main__":
    train()
