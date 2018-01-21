CREATE TABLE loaded_reports (
    load_dt TIMESTAMP,
    report_name VARCHAR(200) PRIMARY KEY,
    report_type VARCHAR(50)
)
;

-- hash index since we will only be using = operator
CREATE INDEX loaded_reports_report_type ON loaded_reports USING hash (report_type);

CREATE TABLE ftci (
  agent_id INTEGER,
  evt_cd_1 INTEGER,
  evt_cd_2 INTEGER,
  dt TIMESTAMP,
  PRIMARY KEY (agent_id, evt_cd_1, evt_cd_2, dt)
)
;

-- hash index since we will only be using = operator
CREATE INDEX ftci_agent_id ON ftci USING hash (agent_id);

-- B-tree indexes for all equality operators (i.e. >=, BETWEEN, IN etc.)
CREATE INDEX ftci_evt_cd_1 ON ftci USING (evt_cd_1);
CREATE INDEX ftci_dt ON ftci USING (dt);


CREATE TABLE csi (
  dt TIMESTAMP,
  queue_id INTEGER,
  metric VARCHAR(10),
  value INTEGER,
  PRIMARY KEY (dt, queue_id, metric)
)
;

CREATE INDEX csi_queue_id ON csi USING (queue_id);
CREATE INDEX csi_dt ON csi USING (dt);
