# -*- coding: utf-8 -*-
"""
Created on Mon May 25 18:59:29 2026

@author: Ignacio Recabal
"""

import pandas as pd
import mysql.connector
import os
from pathlib import Path
from dotenv import load_dotenv
import logging
from config import VALID_CLIENTS, VALID_TYPE
import smtplib
from email.message import EmailMessage

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s",
    filename="etl.log",
)

# Bulk UPSERT query

insert_query = """
INSERT INTO logistics (
    client_name,
    client_type,
    product_name,
    quantity,
    delivery_date,
    created_by
)

VALUES (%s, %s, %s, %s, %s, %s)

ON DUPLICATE KEY UPDATE

    quantity = VALUES(quantity),
    client_type = VALUES(client_type),
    updated_by = 'python system'
"""


# We define functions that will be used during this project:
    
def normalize_columns(df):
    """
     Normalize dataframe column names.
     """
    df.columns = df.columns.str.strip().str.lower()
    return df    

def validate_clients(df, valid_clients):
    """
    Filter dataframe using valid clients list.
    """

    df = df[df["client_name"].isin(valid_clients)]

    return df


def validate_type(df, valid_type):
    """
    Filter dataframe using valid order types.
    """

    df = df[df["client_type"].isin(valid_type)]

    return df
    
def extract_data(base_path):
    
    """
    Extract orders data from Excel file.
    """
    logging.info("ETL process started")

    try:

        orders = pd.read_excel(
            base_path / "Orders.xlsx"
        )

        orders["delivery_date"] = (
            pd.to_datetime(
                orders["delivery_date"]
            ).dt.strftime("%Y-%m-%d")
        )

        logging.info(
            f"Excel loaded successfully: {len(orders)} rows found"
        )

        return orders

    except FileNotFoundError as e:

        logging.error(
            f"File not found: {e}"
        )

        return None 
    
def transform_data(orders, base_path):
    """
    Transform the excel data and create csv
    """

    orders = normalize_columns(orders)
    
    orders["client_type"] = (
    orders["client_type"]
    .str.strip()
    .str.title()
    )

    required_columns = [
        "client_name",
        "client_type",
        "product_name",
        "quantity",
        "delivery_date",
    ]

    for col in required_columns:

        if col not in orders.columns:

            raise KeyError(
                f"Missing column: {col}"
            )

    invalid_clients = orders[
        ~orders["client_name"].isin(
            VALID_CLIENTS
        )
    ]
    
    invalid_types = orders[
        ~orders["client_type"].isin(
            VALID_TYPE
        )
    ]

    invalid_clients.to_csv(
        base_path / "invalid_clients.csv",
        index=False
    )
    
    invalid_types.to_csv(
    base_path / "invalid_types.csv",
    index=False
    )

    orders = validate_clients(
        orders,
        VALID_CLIENTS
    )

    orders = validate_type(
        orders,
        VALID_TYPE
    )
    
    if len(invalid_clients) > 0:
        logging.warning(
            f"{len(invalid_clients)} invalid clients found"
            )
        
    if len(invalid_types) > 0:    
        logging.warning(
            f"{len(invalid_types)} invalid types found"
            )
        
    return orders, invalid_clients, invalid_types
       

def prepare_insert_values(row):
    """
   Prepare row values for bulk UPSERT.
    """
    values = (
        row.client_name,
        row.client_type,
        row.product_name,
        row.quantity,
        row.delivery_date,
        "python system",
    )

    return values

def load_to_db(orders):
    
    """
    Load transformed orders into MySQL
    using bulk UPSERT.
    """

    insert_values = []

    connection = None
    cursor = None

    try:

        connection = mysql.connector.connect(
            host="localhost",
            user=os.getenv("DB_USER"),
            password=os.getenv("DB_PASSWORD"),
            database=os.getenv("DB_NAME"),
        )

        cursor = connection.cursor()

        # Prepare rows for bulk UPSERT

        for row in orders.itertuples(index=False):

            insert_values.append(
                prepare_insert_values(row)
            )

        logging.info(
            "All orders prepared for UPSERT"
        )

        if insert_values:

            cursor.executemany(
                insert_query,
                insert_values
            )

            logging.info(
                f"{len(insert_values)} orders processed with UPSERT"
            )

        connection.commit()

        logging.info(
            "Database updated successfully"
        )

        # Execute logistics priority procedure

        cursor.execute(
            "CALL proc_logistics_group()"
        )

        connection.commit()

        logging.info(
            "SQL procedure executed successfully"
        )

    except mysql.connector.Error:

        logging.exception("Database load failed")

    finally:

        if cursor:
            cursor.close()

        if connection:
            connection.close()

        logging.info(
            "Database connection closed"
        )
        
def send_email_alert(invalid_clients):
    """
    Send email alert when invalid clients are detected.
    """
    try:

        if len(invalid_clients) > 0:

            EMAIL_USER = os.getenv(
                "EMAIL_USER"
            )

            EMAIL_RECEIVER = os.getenv(
                "EMAIL_RECEIVER"
            )

            EMAIL_PASSWORD = os.getenv(
                "EMAIL_PASSWORD"
            )
            SMTP_PORT = int(os.getenv(
                "SMTP_PORT")
            )

            msg = EmailMessage()

            msg["Subject"] = (
                "Invalid clients detected"
            )

            msg["From"] = EMAIL_USER

            msg["To"] = EMAIL_RECEIVER

            msg.set_content(
                f"{len(invalid_clients)} invalid clients found."
            )

            with smtplib.SMTP_SSL(
                "smtp.gmail.com",
                SMTP_PORT
                
            ) as smtp:

                smtp.login(
                    EMAIL_USER,
                    EMAIL_PASSWORD
                )

                smtp.send_message(msg)

            logging.info(
                "Invalid clients email sent"
            )

        else:

            logging.info(
                "No invalid clients detected"
            )

    except smtplib.SMTPException:

        logging.exception(
            "Email alert failed"
        )  

# now we create main def that will be used along the script.


def main():

    base_path = (
    Path(__file__).parent / "Data"
        )

    load_dotenv(
    Path(__file__).parent / ".env"
        )
    
    orders = extract_data(base_path)

    if orders is None:
        return

    orders, invalid_clients, invalid_types = transform_data(
    orders,
    base_path
        )

    load_to_db(orders)

    send_email_alert(invalid_clients)


if __name__ == "__main__":
    main()
    
 