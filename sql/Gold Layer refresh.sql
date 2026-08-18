--Also Named as Gold_Warehouse_build.sql
TRUNCATE TABLE GOLD.kards;
INSERT INTO GOLD.kards
SELECT * FROM KardsLakehouse.silver.kards;

TRUNCATE TABLE GOLD.spawnables;
INSERT INTO GOLD.spawnables
SELECT * FROM KardsLakehouse.silver.spawnables;

TRUNCATE TABLE GOLD.forecast;
INSERT INTO GOLD.forecast
SELECT * FROM KardsLakehouse.silver.forecast;

TRUNCATE TABLE GOLD.exile;
INSERT INTO GOLD.exile
SELECT * FROM KardsLakehouse.silver.exile;

TRUNCATE TABLE GOLD.synergy_combo_rules;
INSERT INTO GOLD.synergy_combo_rules
SELECT * FROM KardsLakehouse.silver.synergy_combo_rules;

TRUNCATE TABLE GOLD.synergy_tag_rules;
INSERT INTO GOLD.synergy_tag_rules
SELECT * FROM KardsLakehouse.silver.synergy_tag_rules;




TRUNCATE TABLE GOLD.spawn_chain;
INSERT INTO GOLD.spawn_chain
SELECT k.CardId, k.CardName, k.CardType, k.CardNation, k.CardRarity,
    k.CardSubType, k.CostToPlay, k.CostToOperate, k.Attack, k.HitPoint,
    k.Keywords, k.CardEffect, k.IsVeteran, k.VeteranCostToOperate,
    k.VeteranAttack, k.VeteranHitPoint, k.VeteranKeywords, k.VeteranEffect,
    k.Status, k.Expansion, k.IsPermanentPool, k.IsSpawnable, k.IsForecastable,
    s.SpawnCardName, s.SpawnCardType, s.SpawnKeywords, s.SpawnCardCost,
    s.SpawnCostToOperate, s.SpawnAttack, s.SpawnHitPoint, s.SpawnCardEffect,
    s.Spawn6KCardName, s.Spawn6KCardEffect, s.Spawn9KCardName, s.Spawn9KCardEffect,
    s.Spawn12KCardName, s.Spawn12KCardEffect, s.childcardid, cast(GETDATE() as date)
FROM KardsLakehouse.silver.kards k
JOIN KardsLakehouse.silver.spawnables s ON k.CardId = s.CardId
WHERE k.IsSpawnable = 1;

TRUNCATE TABLE GOLD.eligible_for_forecast;
INSERT INTO GOLD.eligible_for_forecast
SELECT * FROM KardsLakehouse.silver.kards WHERE IsForecastable = 1;

TRUNCATE TABLE GOLD.veteran_cards;
INSERT INTO GOLD.veteran_cards
SELECT * FROM KardsLakehouse.silver.kards WHERE IsVeteran = 1;

TRUNCATE TABLE GOLD.permanent_pool_cards;
INSERT INTO GOLD.permanent_pool_cards
SELECT * FROM KardsLakehouse.silver.kards WHERE IsPermanentPool = 1;


TRUNCATE TABLE GOLD.exile_data;
select k.CardId, k.CardName, k.CardType, k.CardNation, k.CardRarity,
    k.CardSubType, k.CostToPlay, k.CostToOperate, k.Attack, k.HitPoint,
    k.Keywords, k.CardEffect, k.IsVeteran, k.VeteranCostToOperate,
    k.VeteranAttack, k.VeteranHitPoint, k.VeteranKeywords, k.VeteranEffect,
    k.Status, k.Expansion, k.IsPermanentPool, k.IsSpawnable, k.IsForecastable,e.ExileCardId,e.AlsoUsedBy
from KardsLakehouse.silver.kards k
join KardsLakehouse.silver.exile e on k.CardId = e.CardId
