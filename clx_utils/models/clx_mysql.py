from mysql.connector import MySQLConnection, Error
import os
from odoo import models
from configparser import ConfigParser
from pathlib import Path


class ClxMysql(models.Model):
    _name = "clx.mysql"
    _description = "Connect to MySql Database"

    def update_contact(self, vals):
        contact = vals.get("contact")
        db_config = self._read_db_config("db.ini", "clxdb")
        update_entity = (
            "UPDATE odoo_entity "
            + " SET entity_name = %(name)s , entity_type = %(company_type)s ,odoo_parent_id = %(parent_id)s "
            + " WHERE odoo_entity_id = %(id)s;"
        )

        data_entity = {
            "name": contact.name,
            "company_type": contact.company_type,
            "parent_id": contact.parent_id.id if contact.parent_id.id else 0,
            "id": contact.id,
        }

        try:
            cnx = MySQLConnection(**db_config)
            cursor = cnx.cursor()
            cursor.execute(update_entity, data_entity)
            cnx.commit()

        except Error as error:
            print(error)

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
            raise Exception("{0} not found in the {1} file".format(section, filename))

        return db
