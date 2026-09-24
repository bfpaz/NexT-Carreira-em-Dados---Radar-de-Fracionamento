CREATE DATABASE neoenergia;

CREATE TYPE tipo_geracao_enum AS ENUM ('UFV', 'UTE');
CREATE TYPE porte_enum AS ENUM ('Microgeração', 'Minigeração');
CREATE TYPE classe_consumo AS ENUM ('Residencial','Comercial' ,'Rural', 'Industrial', 'Poder público',
'Serviço público', 'Iluminação pública');
CREATE TYPE subgrupo_tarifario AS ENUM ('B1', 'B3', 'B2', 'A4', 'B4', 'AS', 'A3');

CREATE TABLE titular (
 id_titular SERIAL PRIMARY KEY,  
 nome_titular VARCHAR(150) NOT NULL,  
 cpf_cnpj VARCHAR(50) NOT NULL
); 

CREATE TABLE municipio (
 id_municipio SERIAL PRIMARY KEY,   
 nome_municipio VARCHAR(50) NOT NULL, 
 estado CHAR(2) NOT NULL, 
 regiao VARCHAR(50) not NULL
); 



CREATE TABLE distribuidora (
 id_distribuidora SERIAL PRIMARY KEY,
 nome_distribuidora VARCHAR(50) NOT NULL  
 ); 

CREATE TABLE usina 
( 
 id_usina SERIAL PRIMARY KEY,  
 id_municipio INT,  
 id_distribuidora INT,  
 id_titular INT,  
 cod_empreendimento VARCHAR(50) NOT NULL,  
 tipo_geracao tipo_geracao_enum NOT NULL,  
 classe_consumo classe_consumo NOT NULL,
 subgrupo_tarifario subgrupo_tarifario NOT NULL,
 potencia_instalada FLOAT NOT NULL,  
 mes_referencia DATE not null,
 UNIQUE (codigo_usina)
); 

ALTER TABLE usina 
  ADD CONSTRAINT fk_usina_municipio 
  FOREIGN KEY (id_municipio) REFERENCES municipio (id_municipio);

ALTER TABLE usina
  ADD CONSTRAINT fk_usina_distribuidora 
  FOREIGN KEY (id_distribuidora) REFERENCES distribuidora (id_distribuidora);

ALTER TABLE usina
  ADD CONSTRAINT fk_usina_titular 
  FOREIGN KEY (id_titular) REFERENCES titular (id_titular);
   
   
CREATE INDEX idx_usina_municipio ON usina(id_municipio);
CREATE INDEX idx_usina_distribuidora ON usina(id_distribuidora);
CREATE INDEX idx_usina_titular ON usina(id_titular);
