from mysql.connector import MySQLConnection, Error
import os
from odoo import models
from configparser import ConfigParser
from pathlib import Path
import logging

_logger = logging.getLogger(__name__)


class ClxMysql(models.Model):
    _name = "clx.mysql"
    _description = "Connect to MySql Database"

    def create_contact(self, vals):
        contact = vals.get("contact")
        db_config = self._read_db_config()
        insert_entity = """INSERT INTO odoo_entity (odoo_entity_id,
                                                   entity_name,
                                                   entity_type,
                                                   odoo_parent_id,
                                                   street,
                                                   city,
                                                   vertical,
                                                   yardi_code)
                           VALUES (%(odoo_entity_id)s,
                                   %(entity_name)s,
                                   NULLIF(%(entity_type)s, "NULL"),
                                   NULLIF(%(odoo_parent_id)s, "NULL"),
                                   NULLIF(%(street)s, "NULL"),
                                   NULLIF(%(city)s, "NULL"),
                                   NULLIF(%(vertical)s, "NULL"),
                                   NULLIF(%(yardi_code)s, "NULL"));"""

        entity_data = {
            "odoo_entity_id": contact.id,
            "entity_name": contact.name,
            "entity_type": contact.company_type if contact.company_type else "NULL",
            "odoo_parent_id": contact.parent_id.id if contact.parent_id.id else "NULL",
            "street": contact.street if contact.street else "NULL",
            "city": contact.city if contact.city else "NULL",
            "vertical": contact.vertical if contact.vertical else "NULL",
            "yardi_code": contact.yardi_code if contact.yardi_code else "NULL",
        }

        try:
            cnx = MySQLConnection(**db_config)
            cursor = cnx.cursor()
            cursor.execute(insert_entity, entity_data)
            cnx.commit()
            _logger.info("CLXDB Contact Created - " + str(entity_data))

        except Error as error:
            _logger.error("CLXDB Contact Create ERROR - " + str(entity_data) + " - " + str(error))

        finally:
            cursor.close()
            cnx.close()

    def update_contact(self, vals):
        contact = vals.get("contact")
        db_config = self._read_db_config()
        update_entity = """UPDATE odoo_entity
                           SET entity_name = %(entity_name)s,
                               entity_type = NULLIF(%(entity_type)s, "Null"),
                               odoo_parent_id = NULLIF(%(odoo_parent_id)s, "Null"), 
                               street = NULLIF(%(street)s, "Null"), 
                               city = NULLIF(%(city)s, "Null"),
                               vertical = NULLIF(%(vertical)s, "Null"),
                               yardi_code = NULLIF(%(yardi_code)s, "Null") 
                           WHERE odoo_entity_id = %(odoo_entity_id)s;"""

        entity_data = {
            "odoo_entity_id": contact.id,
            "entity_name": contact.name,
            "entity_type": contact.company_type if contact.company_type else "NULL",
            "odoo_parent_id": contact.parent_id.id if contact.parent_id.id else "NULL",
            "street": contact.street if contact.street else "NULL",
            "city": contact.city if contact.city else "NULL",
            "vertical": contact.vertical if contact.vertical else "NULL",
            "yardi_code": contact.yardi_code if contact.yardi_code else "NULL",
        }

        try:
            cnx = MySQLConnection(**db_config)
            cursor = cnx.cursor()
            cursor.execute(update_entity, entity_data)
            cnx.commit()
            _logger.info("CLXDB Contact Updated - " + str(entity_data))

        except Error as error:
            _logger.error("CLXDB Contact Update ERROR - " + str(entity_data) + " - " + str(error))

        finally:
            cursor.close()
            cnx.close()

    def _read_db_config(self):
        mysql_host = self.env["ir.config_parameter"].sudo().get_param("mysql_host", "")
        mysql_database = self.env["ir.config_parameter"].sudo().get_param("mysql_database", "")
        mysql_user = self.env["ir.config_parameter"].sudo().get_param("mysql_user", "")
        mysql_password = self.env["ir.config_parameter"].sudo().get_param("mysql_password", "")

        db = {
            "host": mysql_host,
            "database": mysql_database,
            "user": mysql_user,
            "password": mysql_password,
        }

        return db
