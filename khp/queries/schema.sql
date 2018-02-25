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

CREATE TABLE transcripts (
  contact_id INTEGER,
  sender TEXT,
  display_name VARCHAR(100),
  dt TIMESTAMP,
  message_type INTEGER,
  message TEXT
)
;


CREATE TABLE enhanced_transcripts (
  contact_id INTEGER,
  handle_time INTEGER,
  wait_time INTEGER,

  khp_message_count INTEGER,
  khp_double_message_count INTEGER, -- count times responded twice in a row
  khp_mean_message_length DECIMAL(6,2),
  khp_max_message_length INTEGER,
  khp_mean_word_count DECIMAL(6,2),
  khp_max_word_count INTEGER,
  khp_sum_word_count INTEGER,

  khp_mean_response_time DECIMAL(5,2), -- in seconds
  khp_max_response_time DECIMAL(5,2),
  khp_median_response_time DECIMAL(5,2),
  khp_sum_response_time DECIMAL(5,2),


  ext_message_count INTEGER,
  ext_double_message_count INTEGER, -- count times responded twice in a row
  ext_mean_message_length DECIMAL(6,2),
  ext_max_message_length INTEGER,
  ext_mean_word_count DECIMAL(6,2),
  ext_max_word_count INTEGER,
  ext_sum_word_count INTEGER,

  ext_mean_response_time DECIMAL(5,2), -- in seconds
  ext_max_response_time DECIMAL(5,2),
  ext_median_response_time DECIMAL(5,2),
  ext_sum_response_time DECIMAL(5,2),

  -- TODO: add survey info!!

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