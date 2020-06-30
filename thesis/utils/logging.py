import logging
from datetime import datetime
import os

def get_logger(name: str) -> logging.Logger:
    #TODO: add docstring
    # set up logging to file - see previous section for more details
    current_time = datetime.now().strftime('%Y-%m-%d-%H:%M:%S')
    
    if not os.path.isdir("./logs"):
        os.mkdir("./logs")

    logging.basicConfig(level=logging.DEBUG,
                        format='%(asctime)s %(name)-12s %(levelname)-8s %(message)s',
                        datefmt='%m-%d %H:%M',
                        filename='./logs/thesis_' + current_time + '.log',
                        filemode='a')

    # define a Handler which writes INFO messages or higher to the sys.stderr
    console = logging.StreamHandler()
    console.setLevel(logging.INFO)
    # set a format which is simpler for console use
    formatter = logging.Formatter('%(name)-12s: %(levelname)-8s %(message)s')
    # tell the handler to use this format
    console.setFormatter(formatter)
    # add the handler to the root logger
    logging.getLogger('').addHandler(console)

    # Now, we can log to the root logger, or any other logger. First the root...
    logging.info('Root logger set up')

    return logging.getLogger(name)
