CREATE DATABASE IF NOT EXISTS covid_db CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;
USE covid_db;

DROP TABLE IF EXISTS usa_county_daily;
DROP TABLE IF EXISTS usa_counties;
DROP TABLE IF EXISTS province_daily;
DROP TABLE IF EXISTS country_daily;
DROP TABLE IF EXISTS country_latest;
DROP TABLE IF EXISTS worldometer;
DROP TABLE IF EXISTS global_daily;
DROP TABLE IF EXISTS countries;

CREATE TABLE countries (
  country_id INT AUTO_INCREMENT PRIMARY KEY,
  name       VARCHAR(100) NOT NULL UNIQUE,
  who_region VARCHAR(50)
);

CREATE TABLE global_daily (
  date                    DATE PRIMARY KEY,
  confirmed               BIGINT,
  deaths                  BIGINT,
  recovered               BIGINT,
  active                  BIGINT,
  new_cases               BIGINT,
  new_deaths              BIGINT,
  new_recovered           BIGINT,
  deaths_per_100_cases    DOUBLE,
  recovered_per_100_cases DOUBLE,
  deaths_per_100_recovered DOUBLE,
  num_countries           INT
);

CREATE TABLE country_latest (
  country_id               INT PRIMARY KEY,
  confirmed                BIGINT,
  deaths                   BIGINT,
  recovered                BIGINT,
  active                   BIGINT,
  new_cases                BIGINT,
  new_deaths               BIGINT,
  new_recovered            BIGINT,
  deaths_per_100_cases     DOUBLE,
  recovered_per_100_cases  DOUBLE,
  deaths_per_100_recovered DOUBLE,
  confirmed_last_week      BIGINT,
  week_change              BIGINT,
  week_pct_increase        DOUBLE,
  FOREIGN KEY (country_id) REFERENCES countries(country_id)
);

CREATE TABLE country_daily (
  country_id    INT NOT NULL,
  date          DATE NOT NULL,
  confirmed     BIGINT,
  deaths        BIGINT,
  recovered     BIGINT,
  active        BIGINT,
  new_cases     BIGINT,
  new_deaths    BIGINT,
  new_recovered BIGINT,
  PRIMARY KEY (country_id, date),
  KEY idx_date (date),
  FOREIGN KEY (country_id) REFERENCES countries(country_id)
);

CREATE TABLE province_daily (
  id             BIGINT AUTO_INCREMENT PRIMARY KEY,
  country_id     INT NOT NULL,
  province_state VARCHAR(100),
  lat            DOUBLE,
  lon            DOUBLE,
  date           DATE NOT NULL,
  confirmed      BIGINT,
  deaths         BIGINT,
  recovered      BIGINT,
  active         BIGINT,
  KEY idx_country_date (country_id, date),
  FOREIGN KEY (country_id) REFERENCES countries(country_id)
);

CREATE TABLE worldometer (
  country_name     VARCHAR(100) PRIMARY KEY,
  continent        VARCHAR(50),
  population       BIGINT,
  total_cases      BIGINT,
  new_cases        BIGINT,
  total_deaths     BIGINT,
  new_deaths       BIGINT,
  total_recovered  BIGINT,
  new_recovered    BIGINT,
  active_cases     BIGINT,
  serious_critical BIGINT,
  cases_per_1m     DOUBLE,
  deaths_per_1m    DOUBLE,
  total_tests      BIGINT,
  tests_per_1m     DOUBLE,
  who_region       VARCHAR(50)
);

CREATE TABLE usa_counties (
  uid            BIGINT PRIMARY KEY,
  iso2           CHAR(2),
  iso3           CHAR(3),
  fips           INT,
  admin2         VARCHAR(100),
  province_state VARCHAR(100),
  lat            DOUBLE,
  lon            DOUBLE,
  combined_key   VARCHAR(200),
  KEY idx_state (province_state)
);

CREATE TABLE usa_county_daily (
  uid       BIGINT NOT NULL,
  date      DATE NOT NULL,
  confirmed BIGINT,
  deaths    BIGINT,
  PRIMARY KEY (uid, date),
  KEY idx_date (date),
  FOREIGN KEY (uid) REFERENCES usa_counties(uid)
)
