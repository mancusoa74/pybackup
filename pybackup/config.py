import os
import sys
import logging
import yamale
import yaml
from pybackup.custom_validators import CustomValidators


log = logging.getLogger(__name__)


def load_config(conf_file):
    cfg = {}
    if not os.path.isfile(conf_file):
        log.critical("Configuration file {} not existing".format(conf_file))
        sys.exit(1)

    try:
        log.info("Reading {} configuration file".format(conf_file))
        with open(conf_file, "r") as config:
            cfg = yaml.safe_load(config)
    except yaml.scanner.ScannerError as e:
        log.error("Syntax error in {}".format(conf_file))
        log.critical("\n {}".format(e))
        sys.exit(1)
    except yaml.parser.ParserError as e:
        log.error("Syntax error in {}".format(conf_file))
        log.critical("\n {}".format(e))
        sys.exit(1)
    return cfg


def validate_config(schema_file, config_file):
    custom_validator = CustomValidators().get_validators()
    try:
        schema = yamale.make_schema(schema_file, validators=custom_validator)
    except IndexError as e:
        log.critical('Yaml schema file is empty')
        sys.exit(1)

    cfg = yamale.make_data(config_file)
    if len(cfg) == 0:
        log.critical('Configuration file is empty')
        sys.exit(1)

    try:
        yamale.validate(schema, cfg)
    except ValueError as e:
        log.critical(e)
        sys.exit(1)


def add_cfg_default(cfg):
    if 'backup_ignore_files' not in cfg:
        cfg['backup_ignore_files'] = []


def load_validate_config(schema_file, config_file):
    cfg = load_config(config_file)
    validate_config(schema_file, config_file)
    add_cfg_default(cfg)

    log.info("Configuration file is valid")
    log.info("Configuration: {}".format(cfg))
    return cfg
