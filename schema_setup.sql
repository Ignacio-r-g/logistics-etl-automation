CREATE SCHEMA logistics_orders;

USE logistics_orders;
DROP TABLE IF EXISTS logistics;
CREATE TABLE logistics (
	order_id INT AUTO_INCREMENT PRIMARY KEY,
    client_name VARCHAR(100),
    client_type VARCHAR(100),
    product_name VARCHAR(100),
    quantity INT,
    delivery_date DATE,
    order_status VARCHAR(100),
    priority_level VARCHAR (100),
    email_status VARCHAR (100),
    created_by VARCHAR (100),
    updated_by VARCHAR (100),
    action_type VARCHAR (50),
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP
    );
    
DROP TABLE IF EXISTS log_order_updates;
    
CREATE TABLE log_order_updates (
    log_id INT AUTO_INCREMENT PRIMARY KEY,
    order_id INT,
    client_name VARCHAR(100),
    client_type VARCHAR (100),
    product_name VARCHAR (100),
    quantity INT,
    delivery_date DATE,
    order_status VARCHAR(100),
    priority_level VARCHAR(100),
    email_status VARCHAR (100),
    created_by VARCHAR(100),
    updated_by VARCHAR (100),
    action_type VARCHAR(50),
    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP
); 