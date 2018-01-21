/*
This query is designed to summarize agent metadata.

For each agent_id,

*/
create temporary table ranks as (
	select
		agent_id,
		evt_cd_1||'-'||evt_cd_2 as evt_cd,
		dt,
		ROW_NUMBER() OVER (PARTITION BY agent_id ORDER BY dt ASC) as row_num
	from ftci
)
;

select
	evt_cd_1||'-->'||evt_cd_2 AS evt,
	count(*) cnt,
	sum(delta) as time_spent
from (
  select
  	r1.agent_id,
  	r1.evt_cd AS evt_cd_1,
  	r2.evt_cd as evt_cd_2,
  --	r2.dt - r1.dt AS delta,
  	ROUND(CAST(EXTRACT(seconds from (r2.dt - r1.dt))/60 +
          EXTRACT(minutes from (r2.dt - r1.dt)) +
          EXTRACT(hours from (r2.dt - r1.dt))*60 AS decimal),2) as delta
  from ranks as r1
  join ranks as r2
  on
  	r1.agent_id=r2.agent_id
  	AND r1.row_num=r2.row_num-1
  ) as summary
group by 1
;

-- discuss with rob
