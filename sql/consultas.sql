-- quantos e quais são os possíveis suspeitos
-- (soma das potencias instaladas no mesmo cpf/cnpj superior ao limite de acordo com porte)?
SELECT COUNT(*) FROM 
(
SELECT t.cpf_cnpj,
	   t.nome_titular,
       u.porte,
       m.nome_municipio,
       COUNT(u.id_usina) AS qtd_usinas,
       SUM(u.potencia_instalada) AS potencia_total
FROM usina u
JOIN titular t ON u.id_titular = t.id_titular
JOIN municipio m ON u.id_municipio = m.id_municipio
WHERE m.estado = 'PE'
GROUP BY t.cpf_cnpj, t.nome_titular, u.porte, m.nome_municipio
HAVING (u.porte = 'Microgeracao' AND SUM(u.potencia_instalada) > 75)
    OR (u.porte = 'Minigeracao' AND SUM(u.potencia_instalada) > 3000)
ORDER BY potencia_total DESC
);


-- Lista de suspeitos por grupo tarifário os grupos por titular, município e porte que excedem os limites de
# potência, incluindo quantidade de empreendimentos e potência acumulada.
SELECT
    t.cpf_cnpj,
    t.nome_titular,
    u.porte,
    m.nome_municipio,
    COUNT(u.id_usina) AS qtd_usinas,
    SUM(u.potencia_instalada) AS potencia_total_kw
FROM usina u
JOIN titular t ON u.id_titular = t.id_titular
JOIN municipio m ON u.id_municipio = m.id_municipio
WHERE m.estado = 'PE'
GROUP BY t.cpf_cnpj, t.nome_titular, u.porte, m.nome_municipio
HAVING
    (u.porte = 'Microgeracao' AND SUM(u.potencia_instalada) > 75)
    OR (u.porte = 'Minigeracao' AND SUM(u.potencia_instalada) > 3000)
ORDER BY potencia_total_kw DESC


-- quanto da potência está sob suspeita?
SELECT SUM(u.potencia_instalada) AS potencia_suspeita
FROM usina u
JOIN municipio m ON u.id_municipio = m.id_municipio
WHERE m.estado = 'PE' --AND u.data_atualizacao_cadastral > '2021-12-31'
  AND u.id_titular IN (
      SELECT id_titular
      FROM usina u2
      JOIN municipio m2 ON u2.id_municipio = m2.id_municipio
      WHERE m2.estado = 'PE'
      GROUP BY u2.id_titular, u2.porte, m2.nome_municipio 
      HAVING (u2.porte = 'Microgeracao' AND SUM(u2.potencia_instalada) > 75)
         OR (u2.porte = 'Minigeracao' AND SUM(u2.potencia_instalada) > 3000)
  );


-- quais são os suspeitos por porte, classe de consumo e subgrupo tarifário?
SELECT
    u.porte,
    u.classe_consumo,
    u.subgrupo_tarifario,
    COUNT(DISTINCT t.id_titular) AS qtd_suspeitos,
    SUM(u.potencia_instalada) AS potencia_total_kw
FROM usina u
JOIN titular t ON u.id_titular = t.id_titular
JOIN municipio m ON u.id_municipio = m.id_municipio
WHERE m.estado = 'PE'
GROUP BY u.porte, u.classe_consumo, u.subgrupo_tarifario
HAVING
    (u.porte = 'Microgeracao' AND SUM(u.potencia_instalada) > 75)
    OR (u.porte = 'Minigeracao' AND SUM(u.potencia_instalada) > 3000)
ORDER BY qtd_suspeitos DESC;

-- evolução mensal de novas usinas e potência
WITH por_mes AS (
  SELECT
    DATE_TRUNC('month', data_atualizacao_cadastral) AS mes,
    COUNT(id_usina) AS novas_usinas_no_mes,
    SUM(potencia_instalada) AS nova_potencia_no_mes
  FROM usina
  WHERE data_atualizacao_cadastral IS NOT NULL
  GROUP BY DATE_TRUNC('month', data_atualizacao_cadastral)
)
SELECT
  mes,
  novas_usinas_no_mes,
  nova_potencia_no_mes,
  SUM(novas_usinas_no_mes) OVER (ORDER BY mes) AS total_usinas_acumulado,
  SUM(nova_potencia_no_mes) OVER (ORDER BY mes) AS potencia_acumulada
FROM por_mes
ORDER BY mes ASC;

-- lista de ceps de titulares suspeitos
WITH titulares_suspeitos AS (
SELECT
    t.id_titular,
    t.cpf_cnpj,
    t.nome_titular,
    u.id_municipio,
    m.nome_municipio,
    u.porte,
    SUM(u.potencia_instalada) AS potencia_total_kw
FROM usina u
JOIN titular t ON u.id_titular = t.id_titular
JOIN municipio m ON u.id_municipio = m.id_municipio
WHERE m.estado = 'PE'
GROUP BY
    t.id_titular,
    t.cpf_cnpj,
    t.nome_titular,
    u.id_municipio,
    m.nome_municipio,
    u.porte
HAVING
    (u.porte = 'Microgeracao' AND SUM(u.potencia_instalada) > 75)
    OR (u.porte = 'Minigeracao' AND SUM(u.potencia_instalada) > 3000)
)
SELECT
ts.cpf_cnpj,
ts.nome_titular,
ts.id_municipio,
ts.nome_municipio,
ts.porte,
u.cod_empreendimento,
NULLIF(regexp_replace(u.cep::text, '\D', '', 'g'), '') AS cep_normalizado,
u.potencia_instalada
FROM usina u
JOIN titulares_suspeitos ts
ON u.id_titular = ts.id_titular
AND u.id_municipio = ts.id_municipio
AND u.porte = ts.porte
WHERE u.cep IS NOT NULL
AND u.cep <> ''
ORDER BY ts.nome_municipio, ts.nome_titular, ts.porte, u.cod_empreendimento;