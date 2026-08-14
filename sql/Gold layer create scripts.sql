----Also Named as Gold_Warehouse_refresh.sql

CREATE schema GOLD;

create table GOLD.spawn_chain
AS
SELECT  k.CardId, k.CardName, k.CardType, k.CardNation, k.CardRarity,
    k.CardSubType, k.CostToPlay, k.CostToOperate, k.Attack, k.HitPoint,
    k.Keywords, k.CardEffect, k.IsVeteran, k.VeteranCostToOperate,
    k.VeteranAttack, k.VeteranHitPoint, k.VeteranKeywords, k.VeteranEffect,
    k.Status, k.Expansion, k.IsPermanentPool, k.IsSpawnable, k.IsForecastable,
    s.SpawnCardName, s.SpawnCardType, s.SpawnKeywords, s.SpawnCardCost,
    s.SpawnCostToOperate, s.SpawnAttack, s.SpawnHitPoint, s.SpawnCardEffect,
    s.Spawn6KCardName, s.Spawn6KCardEffect, s.Spawn9KCardName, s.Spawn9KCardEffect,
    s.Spawn12KCardName, s.Spawn12KCardEffect, s.childcardid, cast(GETDATE() as date) createddate
from KardsLakehouse.silver.kards k
join KardsLakehouse.silver.spawnables s on k.CardId = s.CardId
where k.IsSpawnable = 1;


create table GOLD.eligible_for_forecast
AS
select *
from KardsLakehouse.silver.kards k
where k.IsForecastable = 1;

create table GOLD.veteran_cards
AS
select *
from KardsLakehouse.silver.kards k
where k.IsVeteran = 1;

create table GOLD.permanent_pool_cards
AS
select *
from KardsLakehouse.silver.kards k
where k.IsPermanentPool = 1;

create table GOLD.kards as SELECT * from KardsLakehouse.silver.kards;
create table GOLD.spawnables as SELECT * from KardsLakehouse.silver.spawnables;
create table GOLD.forecast as SELECT * from KardsLakehouse.silver.forecast;





