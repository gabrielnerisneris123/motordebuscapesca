"""
Dicionário de termos de pesca esportiva brasileira para classificação de entidades.
O sistema aprende novos termos durante as coletas e expande esses dicionários.
"""

ESPECIES = [
    # Carpas
    "carpa", "carpa comum", "carpa capim", "carpa cabeça grande", "carpa prateada",
    "carpa koi", "amur", "carpa espelho",
    # Tilápias
    "tilápia", "tilapia", "tilápia do nilo", "tilápia vermelha",
    # Tucunarés
    "tucunaré", "tucunare", "tucunaré açu", "tucunaré comum", "tucunaré azul",
    # Dourados
    "dourado", "dorado",
    # Tambaquis e família
    "tambaqui", "pacu", "pacu comum", "pacu brachypomus", "caranha",
    "pirapitinga", "piaractus",
    # Pintados / Surubins
    "pintado", "surubim", "cachara", "jaú", "bagre", "piraíba",
    "barbado", "filhote", "piramutaba",
    # Traíras e afins
    "traíra", "traira", "jeju", "tamuatá",
    # Lambaris
    "lambari", "piaba",
    # Piranha
    "piranha", "piranha vermelha", "piranha preta",
    # Robalo
    "robalo", "robalo peba", "robalo flexa",
    # Corvina
    "corvina",
    # Tainha
    "tainha",
    # Peixe-espada
    "peixe espada", "espada",
    # Ciclídeos
    "oscar", "cará",
    # Piau
    "piau", "piau gordura", "piau três pintas",
    # Curimba
    "curimba", "curimbatá",
    # Matrinxã
    "matrinxã", "matrinxa", "brycon",
    # Pirarucu
    "pirarucu", "arapaima",
    # Outros
    "jundiá", "jundia", "cará", "acará", "acara", "birú", "sarapó",
    "candiru", "cascudo", "pleco", "bodó", "acari",
]

INGREDIENTES = [
    # Farinhas
    "farinha de milho", "fubá", "fuba", "flocão", "flocos de milho",
    "farinha de trigo", "farinha de mandioca", "farinha de peixe",
    "farinha de camarão", "farinha de amendoim", "farinha de soja",
    "farinha de aveia", "farinha de arroz", "farinha de batata",
    "farinha de centeio", "farinha de cevada",
    # Cereais
    "aveia", "aveia em flocos", "granola", "cevada", "sorgo",
    "triguilho", "alpiste", "milheto",
    # Proteínas
    "soja", "farelo de soja", "torresmo", "carne seca", "toucinho",
    "sardinha", "atum", "anchova",
    # Frutas e derivados
    "banana", "banana passa", "manga", "goiaba", "maçã", "pêra",
    "uva", "coco", "abacaxi", "mamão", "melancia",
    # Leguminosas
    "milho", "milho cozido", "milho fermentado", "quirera",
    "feijão", "ervilha", "amendoim", "amendoim torrado",
    # Derivados lácteos
    "leite", "queijo", "iogurte", "creme de leite", "manteiga",
    # Doces e melados
    "melaço", "melado", "rapadura", "açúcar mascavo", "mel",
    "garapa", "caldo de cana",
    # Rações comerciais
    "ração de peixe", "ração de carpa", "ração de tilápia",
    "ração de bagre", "pellet", "extrusado",
    # Fermentados
    "milho fermentado", "trigo fermentado", "quirera fermentada",
    "massa fermentada", "pastão fermentado",
    # Ingredientes especiais
    "anis", "funcho", "canela", "cravo", "pimenta", "gengibre",
    "alho", "cebola", "cominho", "erva-doce",
    # Atrativos industriais
    "betaína", "betaina", "aminoácido", "amino", "L-lisina",
    "nucleotídeo", "extrato de levedura",
    # Óleos
    "óleo de amendoim", "óleo de girassol", "óleo de coco",
    "óleo de peixe", "óleo essencial", "óleo de anis",
]

AROMAS = [
    "anis", "erva-doce", "baunilha", "canela", "mel", "morango",
    "banana", "coco", "laranja", "limão", "frutas vermelhas",
    "caramelo", "chocolate", "uva", "sangue", "fígado", "camarão",
    "sardinha", "alho", "amendoim", "rum", "whisky", "conhaque",
    "menta", "hortelã", "manjericão", "tomilho", "pimenta",
    "milho verde", "milho fermentado", "melaço", "melado",
    "noz moscada", "gengibre", "cravo", "funcho",
]

TECNICAS = [
    # Modalidades
    "pesca de fundo", "pesca de superfície", "pesca de meio d'água",
    "pesca embarcada", "pesca de margem", "pesca em rio",
    "pesca em lago", "pesca em açude", "pesca esportiva",
    "pesca com anzol", "pesca com tarrafa", "pesca com rede",
    # Carpa específico
    "hair rig", "boilie", "method feeder", "spod", "spomb",
    "chum", "groundbait", "pellet rig", "inline lead",
    "running rig", "bolt rig", "zig rig", "pop-up",
    "surface fishing", "stalking", "pesca de carpa",
    # Iscas artificiais
    "spinning", "jigging", "trolling", "fly fishing",
    "pesca com mosca", "pesca de arrasto", "ultralight",
    "pesca com plug", "pesca com minnow",
    # Técnicas gerais
    "ledger", "float fishing", "feeder", "match fishing",
    "pesca de berço", "pesca com bóia", "pesca com chumbada",
    "pesca ao fundo", "pesca à deriva",
    # Fermentação
    "fermentação", "pastão", "massa de pesca", "massa caseira",
]

EQUIPAMENTOS = [
    # Varas
    "vara de pesca", "vara de carpa", "carp rod", "espinhel",
    "vara de spinning", "vara de ultralight", "vara de fly",
    "vara de bait", "vara telescópica", "vara de nylon",
    # Molinetes
    "molinete", "carretilha", "baitcaster", "freespool",
    "big pit", "molinete de carpa",
    # Linha
    "linha de pesca", "multifilamento", "fluorocarbon",
    "nylon", "braid", "linha de ponta",
    # Anzóis
    "anzol", "gancho", "anzol curvo", "wide gape",
    "anzol krank", "anzol de bolie",
    # Chumbadas
    "chumbada", "chumbo", "flat pear", "inline",
    "chumbada lead clip", "distance lead",
    # Acessórios
    "swivel", "girador", "clip de chumbo", "anel de ligação",
    "alarme", "bite alarm", "pod", "bankstick",
    "saco de isca", "pva bag", "pva mesh", "spod mix",
    "rede de pesca", "puçá", "landing net",
    "unhooking mat", "sling", "weighing sling",
    "indicador de toque", "hanger", "bobbin",
    # Eletrônicos
    "sonar", "ecobatímetro", "fishfinder", "gps",
    # Vestimenta
    "colete salva vidas", "bota de pesca", "wader",
]

LOCAIS = [
    # Tipos de locais
    "pesqueiro", "lago", "açude", "represa", "reservatório",
    "rio", "córrego", "riacho", "lagoa", "charco", "brejo",
    "viveiro", "tanque", "porto", "baía",
    # Regiões com pesca
    "pantanal", "amazônia", "cerrado", "mata atlântica",
    "rio são francisco", "rio paraná", "rio araguaia",
    "rio tocantins", "rio paraguai", "rio iguaçu",
    "litoral", "costa", "mar",
]

EVENTOS = [
    "campeonato", "torneio", "copa", "festival", "feira",
    "exposição", "concurso", "competição", "pesca esportiva",
    "ranking", "circuito",
]

CATEGORIAS_CONTEUDO = [
    "receita de isca", "técnica de pesca", "relato de captura",
    "notícia", "review de produto", "dica de pesca",
    "comportamento de peixe", "legislação", "preservação",
    "manejo", "identificação de espécie", "pesca noturna",
    "pesca diurna", "sazonalidade", "condições climáticas",
]

# Termos que indicam conteúdo relevante de pesca
TERMOS_RELEVANCIA = [
    "pesca", "peixe", "pescaria", "pescador", "anzol",
    "vara de pesca", "molinete", "carretilha", "linha", "isca",
    "carpa", "tilápia", "tucunaré", "pintado", "dourado",
    "boilie", "pellet", "groundbait", "feeder", "hair rig",
    "pesqueiro", "captura", "soltar", "pescar",
]

# Termos de exclusão (conteúdo irrelevante)
TERMOS_EXCLUSAO = [
    "receita culinária sem peixe", "minecraft", "pokémon",
]

# Queries iniciais para descoberta de fontes
QUERIES_BUSCA = [
    "pesca esportiva brasileira",
    "pesca de carpa brasil",
    "pesca de tilápia dicas",
    "isca para carpa receita",
    "pesca esportiva forum",
    "pesqueiro brasil",
    "técnica pesca carpa",
    "massa para pesca receita caseira",
    "boilie caseiro receita",
    "pesca de tucunaré",
    "pesca pantanal",
    "equipamentos pesca esportiva",
    "pesca de fundo técnicas",
    "carp fishing brasil",
    "pesca no rio paraná",
    "fermentado para pesca",
    "groundbait caseiro pesca",
    "pesca de competition carpa",
    "isca natural para peixe",
    "atrativo para pesca",
    "aromas para isca pesca",
    "ingredientes massa pesca",
    "pesca forum brasil",
    "blog pesca esportiva",
    "captura e soltura pesca",
    "match fishing brasil",
    "pellet pesca carpa",
    "pesca rio amazon",
    "espécies peixe brasil",
    "revista pesca esportiva",
    "hair rig montagem pesca",
    "pesca spinning brasil",
    "ultralight fishing brasil",
    "pesca de pacu",
    "pesca de pintado",
    "pesca de dourado rio",
    "pesca noturna dicas",
    "melhor isca para carpa",
    "pesca de margem rio",
    "pesca embarcada brasil",
]

# Seeds iniciais de fontes conhecidas sobre pesca brasileira
SEEDS_FONTES = [
    "https://www.pescaeaqua.com.br",
    "https://www.revistapescaesportiva.com.br",
    "https://www.carpabrasil.com.br",
    "https://www.fishingbrasil.com.br",
    "https://www.pesqueiro.com.br",
    "https://www.tunapesca.com.br",
    "https://www.pescador.com.br",
    "https://www.carpfishing.com.br",
    "https://www.pesqueirobrasil.com.br",
    "https://forum.pescaesportiva.net",
    "https://www.blogdopescador.com.br",
    "https://www.pescaemfoco.com.br",
]
