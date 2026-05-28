## ====================================================================================================================================================
## Logistics and retail companies often manage delivery tracking manually in Excel, which can lead to delays, duplicates, and a lack of traceability.
## ====================================================================================================================================================

##																           Objective
## ====================================================================================================================================================================================
## Create a logistics tracking system using MySQL, SQL automation, and Python to improve delivery control and operational reminders through Excel-based operational workflows.
## ====================================================================================================================================================================================


## ====================================================================================================================================================================================
## The system uses MySQL triggers to automatically maintain an audit history table (`log_order_updates`) after every INSERT and UPDATE operation performed on the logistics table.
## ====================================================================================================================================================================================


## ================================================================
##				Database Triggers
## ================================================================

--	 This ensures full operational traceability by recording:
--	- who modified the order
--	- what was changed
--	- when the modification occurred
--	- the type of action executed


USE logistics_orders;
    
DROP TRIGGER IF EXISTS trg_order_insert;
DELIMITER //

CREATE TRIGGER trg_order_insert
AFTER INSERT ON logistics
FOR EACH ROW 
	BEGIN
    INSERT INTO log_order_updates (order_id,client_name, client_type, product_name, quantity,delivery_date,
				order_status, priority_level, email_status, updated_by, created_by, action_type)
                
    VALUES (NEW.order_id, NEW.client_name, NEW.client_type,NEW.product_name, NEW.quantity,NEW.delivery_date,
			NEW.order_status, NEW.priority_level, NEW.email_status, NEW.updated_by, NEW.created_by, "INSERT");
    END //
    
    DELIMITER ;
    
INSERT INTO logistics (client_name,client_type,product_name,quantity,delivery_date,created_by)
VALUES ("Falabella","Existing","Perfume",150,"2026-06-25","localhost");

DROP TRIGGER IF EXISTS trg_order_audit;
DELIMITER //

CREATE TRIGGER trg_order_audit
AFTER UPDATE ON logistics
FOR EACH ROW 
	BEGIN
    INSERT INTO log_order_updates (order_id, client_name, client_type, product_name, quantity, delivery_date, 
				order_status, priority_level, email_status, updated_by, created_by, action_type)
                
    VALUES (NEW.order_id, NEW.client_name, NEW.client_type, NEW.product_name,NEW.quantity, NEW.delivery_date,
			NEW.order_status, NEW.priority_level,NEW.email_status,NEW.updated_by, OLD.created_by, "UPDATE");
    END //
    
    DELIMITER ;
    
UPDATE logistics
SET order_status = "Pending",
	priority_level = "Medium",
    email_status = "Pending",
	updated_by = "localhost"
    WHERE order_id = 1;
    
    
## ====================================================================
## 							Stored Procedure
## ====================================================================

--	A stored procedure (`proc_logistics_group`) automatically assigns operational priority levels based on the order type:

--	- Emergency → High-	- Existing → Medium
--	- New → Low

--	This business logic is centralized inside MySQL to guarantee consistency across all incoming records processed by the ETL pipeline.

DROP PROCEDURE IF EXISTS proc_logistics_group;
SET SQL_SAFE_UPDATES = 0;
DELIMITER //
	CREATE PROCEDURE proc_logistics_group()
	BEGIN
	UPDATE logistics
    SET priority_level = "High", updated_by = "system_procedure"
    WHERE client_type =  "Emergency";
    
    UPDATE logistics
    SET priority_level = "Medium", updated_by = "system_procedure"
    WHERE client_type =  "Existing"; 
    
    UPDATE logistics
	SET priority_level = 'Low', updated_by = "system_procedure"
	WHERE client_type = 'New';
                     
  END //
  
  DELIMITER ;
  CALL proc_logistics_group();
  SELECT
	client_type,
    quantity,
    priority_level    
FROM logistics;

# =================================================
#				Event Scheduler
# =================================================

--	A weekly MySQL Event Scheduler automatically flags deliveries requiring operational follow-up by updating the `email_status` field for orders approaching their delivery date.

DROP EVENT IF EXISTS ev_friday_reminder;
SET GLOBAL event_scheduler = ON;
CREATE EVENT ev_friday_reminder
ON SCHEDULE EVERY 1 WEEK
STARTS "2026-05-29 12:00:00"
DO
	UPDATE logistics
    SET email_status = "Pending", updated_by = "system_event"
    WHERE delivery_date <= CURDATE() + INTERVAL 7 DAY
    AND email_status != "Sent";
    
    
# =================================================
#				Data Integrity
# =================================================    

--	 A UNIQUE constraint prevents duplicate operational records by validating the combination of:
--	- client_name
--	- product_name
--	- delivery_date

--	This enables safe UPSERT operations from Python without creating duplicated orders.
    
ALTER TABLE logistics
ADD CONSTRAINT unique_order
UNIQUE (
    client_name,
    product_name,
    delivery_date
);    
    
    