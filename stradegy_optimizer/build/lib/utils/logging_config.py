import logging
import logging.config
import yaml
import os

def setup_logging(default_path='logging.yaml', default_level=logging.INFO, env_key='LOG_CFG'):
    """
    Setup logging configuration.
    """
    path = os.getenv(env_key, default_path)
    if os.path.exists(path):
        with open(path, 'rt') as f:
            try:
                config = yaml.safe_load(f.read())
                logging.config.dictConfig(config)
            except Exception as e:
                print(e)
                print('Error in Logging Configuration. Using default configs')
                logging.basicConfig(level=default_level)
    else:
        logging.basicConfig(level=default_level)
        print('Failed to load logging configuration file. Using default configs')

def create_default_logging_config():
    """
    Creates a default logging.yaml file if one doesn't exist.
    """
    if not os.path.exists('logging.yaml'):
        logging_config = {
            'version': 1,
            'disable_existing_loggers': False,
            'formatters': {
                'standard': {
                    'format': '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
                },
            },
            'handlers': {
                'console': {
                    'class': 'logging.StreamHandler',
                    'formatter': 'standard'
                },
                'file': {
                    'class': 'logging.handlers.RotatingFileHandler',
                    'formatter': 'standard',
                    'filename': 'logs/system.log',
                    'maxBytes': 10485760, # 10MB
                    'backupCount': 5,
                    'encoding': 'utf8'
                }
            },
            'root': {
                'handlers': ['console', 'file'],
                'level': 'INFO'
            }
        }
        with open('logging.yaml', 'w') as f:
            yaml.dump(logging_config, f, default_flow_style=False)

