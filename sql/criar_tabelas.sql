DROP TABLE IF EXISTS empreendimentos, municipios, distribuidora, titulares CASCADE;

DROP TYPE IF EXISTS porte_enum CASCADE;
DROP TYPE IF EXISTS classe_consumo_enum CASCADE;
DROP TYPE IF EXISTS subgrupo_tarifario_enum CASCADE;

CREATE TYPE porte_enum AS ENUM ('Microgeracao', 'Minigeracao');
CREATE TYPE classe_consumo_enum AS ENUM (
    'Residencial',
    'Comercial',
    'Rural',
    'Industrial',
    'Poder Público',
    'Serviço Público',
    'Iluminação pública'
);
CREATE TYPE subgrupo_tarifario_enum AS ENUM (
    'A1', 'A2', 'A3', 'A3a', 'A4', 'AS', 'B1', 'B2', 'B3', 'B4'
);

CREATE TABLE titulares (
    "idTitular" SERIAL PRIMARY KEY,
    "NumCPFCNPJ" VARCHAR(20) NOT NULL UNIQUE,
    "NomTitularEmpreendimento" VARCHAR(150)
);

CREATE TABLE distribuidora (
    "idDistribuidora" SERIAL PRIMARY KEY,
    "NumCNPJDistribuidora" VARCHAR(20) NOT NULL UNIQUE,
    "SigAgente" VARCHAR(100),
    "NomAgente" VARCHAR(150)
);

CREATE TABLE municipios (
    "idMunicipio" SERIAL PRIMARY KEY,
    "NomMunicipio" VARCHAR(100) NOT NULL,
    "SigUF" CHAR(2) NOT NULL,
    "NomRegiao" VARCHAR(50) NOT NULL,
    CONSTRAINT municipio_nome_uf_regiao_unico
        UNIQUE ("NomMunicipio", "SigUF", "NomRegiao")
);

CREATE TABLE empreendimentos (
    "idEmpreendimento" SERIAL PRIMARY KEY,
    "idTitular" INT NOT NULL,
    "idDistribuidora" INT NOT NULL,
    "idMunicipio" INT NOT NULL,
    "CodEmpreendimento" VARCHAR(50) NOT NULL UNIQUE,
    "DscClasseConsumo" classe_consumo_enum,
    "DscSubGrupoTarifario" subgrupo_tarifario_enum,
    "MdaPotenciaInstaladaKW" DOUBLE PRECISION,
    "AnmPeriodoReferencia" VARCHAR(20),
    "DscPorte" porte_enum,
    "CodCEP" VARCHAR(15),
    "QtdUCRecebeCredito" INT,
    "DthAtualizaCadastralEmpreend" DATE,
    "DscModalidadeHabilitado" VARCHAR(100),
    CONSTRAINT fk_empreendimentos_titular
        FOREIGN KEY ("idTitular") REFERENCES titulares ("idTitular"),
    CONSTRAINT fk_empreendimentos_distribuidora
        FOREIGN KEY ("idDistribuidora") REFERENCES distribuidora ("idDistribuidora"),
    CONSTRAINT fk_empreendimentos_municipio
        FOREIGN KEY ("idMunicipio") REFERENCES municipios ("idMunicipio")
);

CREATE INDEX idx_empreendimentos_titular
    ON empreendimentos ("idTitular");
CREATE INDEX idx_empreendimentos_distribuidora
    ON empreendimentos ("idDistribuidora");
CREATE INDEX idx_empreendimentos_municipio
    ON empreendimentos ("idMunicipio");
