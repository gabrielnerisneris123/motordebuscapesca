-- Inicialização do banco de dados Motor de Busca Pesca Esportiva
-- Executado automaticamente pelo Docker na primeira inicialização

-- Extensões úteis
CREATE EXTENSION IF NOT EXISTS pg_trgm;  -- busca textual por similaridade
CREATE EXTENSION IF NOT EXISTS unaccent; -- busca sem acentos

-- Configuração de busca para português
-- (as tabelas são criadas pelo SQLAlchemy via init_db())

-- Índices adicionais de performance
-- (executados após as tabelas serem criadas)
