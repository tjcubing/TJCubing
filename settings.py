# TJ's servers default to 1.05 MB (experimentally tested with binary search)
# Precisely somewhere between 1.0483 and 1.0484
# Therefore, if you want to capture a HTTP 413 error you must set MAX_CONTENT_LENGTH to be less than 1.05 MB
MAX_CONTENT_LENGTH = 0.9 * 1024 * 1024 #0.9 MB
SITEMAP_INCLUDE_RULES_WITHOUT_PARAMS = True
UPLOADS_DEFAULT_DEST = "/uploads/"
