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
        db_config = self._read_db_config("db.ini", "clxdb")
        update_entity = (
            "INSERT INTO odoo_entity (odoo_entity_id, entity_name, entity_type, odoo_parent_id,"
            + "                       street, city, vertical, yardi_code) "
            + " VALUES (%(odoo_entity_id)s, %(entity_name)s, %(entity_type)s,%(odoo_parent_id)s, "
            + "         %(street)s,%(city)s,%(vertical)s,%(yardi_code)s) "
        )

        data_entity = {
            "odoo_entity_id": contact.id,
            "entity_name": contact.name,
            "entity_type": contact.company_type,
            "odoo_parent_id": contact.parent_id.id if contact.parent_id.id else 0,
            "street": contact.street,
            "city": contact.city,
            "vertical": contact.vertical,
            "yardi_code": contact.yardi_code,
        }

        try:
            cnx = MySQLConnection(**db_config)
            cursor = cnx.cursor()
            cursor.execute(update_entity, data_entity)
            cnx.commit()
            _logger.info("CLXDB Contact Created - " + str(data_entity))

        except Error as error:
            _logger.error("CLXDB Contact Create ERROR - " + str(data_entity) + " - " + str(error))

        finally:
            cursor.close()
            cnx.close()

    def update_contact(self, vals):
        contact = vals.get("contact")
        db_config = self._read_db_config("db.ini", "clxdb")
        update_entity = (
            "UPDATE odoo_entity "
            + " SET entity_name = %(entity_name)s , entity_type = %(entity_type)s ,odoo_parent_id = %(odoo_parent_id)s, "
            + "     street = %(street)s, city = %(city)s, vertical = %(vertical)s, yardi_code = %(yardi_code)s "
            + " WHERE odoo_entity_id = %(odoo_entity_id)s;"
        )

        data_entity = {
            "odoo_entity_id": contact.id,
            "entity_name": contact.name,
            "entity_type": contact.company_type,
            "odoo_parent_id": contact.parent_id.id if contact.parent_id.id else 0,
            "street": contact.street,
            "city": contact.city,
            "vertical": contact.vertical,
            "yardi_code": contact.yardi_code,
        }

        try:
            cnx = MySQLConnection(**db_config)
            cursor = cnx.cursor()
            cursor.execute(update_entity, data_entity)
            cnx.commit()
            _logger.info("CLXDB Contact Updated - " + str(data_entity))

        except Error as error:
            _logger.error("CLXDB Contact Update ERROR - " + str(data_entity) + " - " + str(error))

        finally:
            cursor.close()
            cnx.close()

    @staticmethod
    def _read_db_config(filename, section):
        model_folder = os.path.join(os.path.dirname(__file__))
        module_parent = Path(model_folder)
        clx_addon_root = Path(module_parent.parent)
        file_path = os.path.join(clx_addon_root.parent, filename)

        db = {}
        config = ConfigParser()
        config.read(file_path)

        if config.has_section(section):
            keys = config.items(section)
            for key in keys:
                db[key[0]] = key[1]
        else:
            _logger.error(
                "CLXDB Connection Failed - {0} not found in the {1} file " + str(section) + " - " + str(filename)
            )

        return db
