import os

# Why use this instead of just using
# Because this is used in the "logger" file. The config itself imports logging, 
# which if imported before this module makes another dirty logger alongside our fancy one.
# So using this hacky workaround to load kinda dynamically
LOG_FAILED_SERVER_GRABS = os.path.isfile(".LOG_FAILED_SERVERS")
