CREATE DATABASE IF NOT EXISTS agri_data_db;
CREATE DATABASE IF NOT EXISTS integration_db;
CREATE DATABASE IF NOT EXISTS decision_db;

CREATE USER IF NOT EXISTS 'springboot'@'%' IDENTIFIED BY 'springboot';
ALTER USER 'springboot'@'%' IDENTIFIED BY 'springboot';

GRANT ALL PRIVILEGES ON agri_data_db.* TO 'springboot'@'%';
GRANT ALL PRIVILEGES ON integration_db.* TO 'springboot'@'%';
GRANT ALL PRIVILEGES ON decision_db.* TO 'springboot'@'%';

FLUSH PRIVILEGES;
