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
  PRIMARY KEY (agent_id,
    evt_cd_1, evt_cd_2, dt)
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

DROP TABLE IF EXISTS contacts;
CREATE TABLE contacts (
  contact_id INTEGER,
  queue_id INTEGER,
  interaction_type VARCHAR(5),
  start_time TIMESTAMP,
  end_time TIMESTAMP,
  contact_group_id INTEGER,
  agent_id INTEGER,
  secondary_agents TEXT,
  recording_identifier VARCHAR(15),
  contact_state INTEGER,
  sender TEXT,
  receiver TEXT,
  contact_group_name VARCHAR(15),
  transcript_downloaded BOOLEAN,
  load_file VARCHAR(100),
  PRIMARY KEY (contact_id, interaction_type)
)
;

DROP TABLE IF EXISTS transcripts;
CREATE TABLE transcripts (
  contact_id INTEGER,
  sender TEXT,
  display_name VARCHAR(100),
  dt TIMESTAMP,
  message_type INTEGER,
  message TEXT
)
;

DROP TABLE IF EXISTS distress_scores;
CREATE TABLE distress_scores (
  contact_id INTEGER,
  score INTEGER
)
;


DROP TABLE IF EXISTS enhanced_transcripts;
CREATE TABLE enhanced_transcripts (
  contact_id INTEGER,

  -- handle/wait time, in minutes
  handle_time DECIMAL(10,2),
  wait_time DECIMAL(10,2),

  khp_message_count INTEGER,
  ext_message_count INTEGER,

  -- count times responded twice in a row
  khp_double_message_count INTEGER,
  ext_double_message_count INTEGER,

  -- word counts aggregated over all messages
  mean_khp_word_count DECIMAL(10,2),
  mean_ext_word_count DECIMAL(10,2),

  max_khp_word_count INTEGER,
  max_ext_word_count INTEGER,

  sum_khp_word_count INTEGER,
  sum_ext_word_count INTEGER,

  -- reponse time statistics, in seconds
  mean_khp_response_time DECIMAL(10,2),
  mean_ext_response_time DECIMAL(10,2),

  max_khp_response_time DECIMAL(10,2),
  max_ext_response_time DECIMAL(10,2),

  median_khp_response_time DECIMAL(10,2),
  median_ext_response_time DECIMAL(10,2),

  sum_khp_response_time DECIMAL(10,2),
  sum_ext_response_time DECIMAL(10,2),
  -- TODO: add survey info!!

  PRIMARY KEY (contact_id)
)
;

CREATE TABLE queue_meta (
  queue_id INTEGER,
  lang_cd char(2),
  platform varchar(20),
  PRIMARY KEY (queue_id)
)
;

INSERT INTO queue_meta VALUES (6020, 'EN', 'MOBILE');
INSERT INTO queue_meta VALUES (6007, 'EN', 'DESKTOP');
INSERT INTO queue_meta VALUES (6021, 'FR', 'MOBILE');
INSERT INTO queue_meta VALUES (6008, 'FR', 'DESKTOP');



DROP TABLE IF EXISTS stat_adr;

CREATE TABLE stat_adr (
  PrimaryKey VARCHAR(200),
  EventTime TIMESTAMP,
  DSTStatus INTEGER,
  SwitchID INTEGER,
  AgentID INTEGER,
  EventType INTEGER,
  EventID INTEGER,
  CurrentState INTEGER,
  LastState INTEGER,
  LastStateDuration INTEGER,
  QueueID INTEGER,
  ContactID INTEGER,
  ContactType INTEGER,
  RouteType INTEGER,
  TargetID INTEGER,
  Reason INTEGER,
  DialledNumber BIGINT,
  AssociatedQueueID INTEGER,
  AgentCallType INTEGER,
  EventSequence INTEGER
)
;


DROP TABLE IF EXISTS stat_cdr;

CREATE TABLE stat_cdr (
  PrimaryKey VARCHAR(200),
  EventTime TIMESTAMP,
  DSTStatus INTEGER,
  ContactID INTEGER,
  EventID INTEGER,
  SwitchID INTEGER,
  ContactType INTEGER,
  CurrentState INTEGER,
  LastState INTEGER,
  LastStateDuration INTEGER,
  QueueID INTEGER,
  IntData1 INTEGER,
  IntData2 INTEGER,
  IntData3 INTEGER,
  IntData4 INTEGER,
  EventSequence INTEGER
)
;


CREATE INDEX agent_id_index ON stat_adr (agentid);
CREATE INDEX contact_id_index ON stat_adr (contactid);
