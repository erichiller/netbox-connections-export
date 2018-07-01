""" init.py """
import os
import sys

ROOT_PATH = os.path.abspath( os.path.join( __file__, "..", ".." ) )
if ROOT_PATH not in sys.path:
    sys.path.append( ROOT_PATH )

