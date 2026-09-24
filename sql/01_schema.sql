CREATE DATABASE neoenergia_divisao;

-- Tipos ENUM
CREATE TYPE tipo_geracao_enum AS ENUM ('UFV', 'UTE');
CREATE TYPE porte_enum AS ENUM ('Microgeracao', 'Minigeracao');
CREATE TYPE classe_consumo AS ENUM (
  'Residencial', 'Comercial', 'Rural', 'Industrial', 'Poder Público',
       'Serviço Público', 'Iluminação pública'
);
CREATE TYPE subgrupo_tarifario AS ENUM ('A1', 'A2', 'A3', 'A3a', 'A4', 'AS', 'B1', 'B2', 'B3', 'B4');

-- Titular
CREATE TABLE titular (
  id_titular SERIAL PRIMARY KEY,
  nome_titular VARCHAR(150) NOT NULL,
  cpf_cnpj VARCHAR(20) NOT NULL UNIQUE
);

-- Município
CREATE TABLE municipio (
  id_municipio SERIAL PRIMARY KEY,
  nome_municipio VARCHAR(50) NOT NULL,
  estado CHAR(2) NOT NULL,
  regiao VARCHAR(50) NOT NULL,
  CONSTRAINT municipio_estado_unico UNIQUE (nome_municipio, estado)
);

-- Distribuidora
CREATE TABLE distribuidora (
  id_distribuidora SERIAL PRIMARY KEY,
  nome_distribuidora VARCHAR(50) NOT NULL UNIQUE
);

-- Usina
CREATE TABLE usina (
  id_usina SERIAL PRIMARY KEY,
  id_municipio INT,
  id_distribuidora INT,
  id_titular INT,
  cod_empreendimento VARCHAR(50) NOT NULL UNIQUE,
  tipo_geracao tipo_geracao_enum NOT NULL,
  classe_consumo classe_consumo NOT NULL,
  subgrupo_tarifario subgrupo_tarifario NOT NULL,
  potencia_instalada FLOAT NOT NULL,
  mes_referencia DATE NOT NULL,
  porte porte_enum NOT NULL,
  cep VARCHAR(15),
  numero_beneficiarios INT,
  data_atualizacao_cadastral DATE,
  CONSTRAINT fk_usina_municipio FOREIGN KEY (id_municipio) REFERENCES municipio (id_municipio),
  CONSTRAINT fk_usina_distribuidora FOREIGN KEY (id_distribuidora) REFERENCES distribuidora (id_distribuidora),
  CONSTRAINT fk_usina_titular FOREIGN KEY (id_titular) REFERENCES titular (id_titular)
);

-- Índices
CREATE INDEX idx_usina_municipio ON usina(id_municipio);
CREATE INDEX idx_usina_distribuidora ON usina(id_distribuidora);
CREATE INDEX idx_usina_titular ON usina(id_titular);
