# ========== Input parameters section ==========

# Minimal time for input plugin to go sleep waiting for next event.
# The higher the value, the more values from the future (equal to the
# parameter value) will be published in advance.
# Сan be considered as batch size. E.g setting parameter to 10 seconds
# will cause to publishing events every 10 seconds from the next 10
# seconds interval. This parameter does not affect the timestamps
# passed to callback at all.
# Parameter is only actual in live mode and ignored for cron input
# plugin.
AHEAD_PUBLICATION_SECONDS = 0.01

# ========== Output parameters section ==========

# Minimal size of output queue with rendered events to perform flush.
FLUSH_AFTER_SIZE = 100

# Timeout after which output queue with rendered events is flushed.
FLUSH_AFTER_SECONDS = 1.0
