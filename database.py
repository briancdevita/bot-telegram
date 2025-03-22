import sqlite3 
from sqlite3 import Error
import logging


logger = logging.getLogger(__name__)



def create_connection():
    """ create a database connection to a SQLite database """
    conn = None
    try:
        conn = sqlite3.connect("reservas.db")
        return conn
    except Error as e:
        logger.error(f"The error '{e}' occurred")

    return conn


def create_table(conn):
    """ create a table """
    try:
        c = conn.cursor()
        c.execute(
            """
            CREATE TABLE IF NOT EXISTS reservations (
                id TEXT PRIMARY KEY,
                user_id INTEGER NOT NULL,
                service TEXT NOT NULL,
                date TEXT NOT NULL,
                time TEXT NOT NULL,
                contact TEXT NOT NULL
              
            )
            """
        )
        conn.commit()
        conn.close()
        print('TABLA CREADA')
    except Error as e:
        logger.error(f"The error '{e}' occurred")



def save_reservation( id, user_id, service, date, time, contact):
    print(contact)



    conn = create_connection()
    if conn is not None:
        try:
            cursor = conn.cursor()
            cursor.execute(
                """
                INSERT INTO reservations (id, user_id, service, date, time, contact)
                VALUES (?, ?, ?, ?, ?, ?)
                """,
                (   id,
                    user_id, 
                    service, 
                    date, 
                    time, 
                    contact
                    )
                    
            )
            conn.commit()
            return True
        except Error as e:
            logger.error(f"The error '{e}' occurred")
            return False
        finally:
            conn.close()
    return False



def delete_reservation(reservation_id):
    print("Resevation from delete_reservation", reservation_id)
    conn = create_connection()
    if conn is not None:
        try:
            cursor = conn.cursor()
            cursor.execute(
                """
                DELETE FROM reservations WHERE id = ?
                """,
                (reservation_id,),
            )
            conn.commit()
            return True
        except Error as e:
            logger.error(f"The error '{e}' occurred")
            return False
        finally:
            conn.close()
    return False


def get_user_reservations(user_id):
    conn = create_connection()
    reservations = []
    if conn is not None:
        try:
            cursor = conn.cursor()

            cursor.execute(
                """
                SELECT * FROM reservations WHERE user_id = ?
                """,
                (user_id,),
            )
            rows = cursor.fetchall()
            columns = ["id", "user_id", "service", "date", "time", "contact"]
            for row in rows:
                reservations.append(dict(zip(columns, row)))
        except Error as e:
            logger.error(f"The error '{e}' occurred")
        finally:
            conn.close()
    return reservations



def check_reservation(reservation_id):
    conn = create_connection()
    if conn is not None:
        try:
            cursor = conn.cursor()

            cursor.execute(
                """
                SELECT * FROM reservations WHERE id = ?
                """,
                (reservation_id,),
            )
            row = cursor.fetchone()
            if row is not None:
                return True
        except Error as e:
            logger.error(f"The error '{e}' occurred")
        finally:
            conn.close()
    return False


def initialize_database():
    print("ENTRE")
    conn = create_connection()
    if conn is not None:
        create_table(conn)
        conn.close()
    else:
        logger.error("Error! cannot create the database connection.")
        return False