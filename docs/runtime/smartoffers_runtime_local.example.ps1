# SmartOffers local runtime template
#
# Copy this file to smartoffers_runtime_local.ps1 for local use.
# The destination file is ignored by Git and must contain only local values.

$env:SMARTOFFERS_QA4_API_URL = "<SMARTOFFERS_QA4_API_URL>"
$env:SMARTOFFERS_QA4_ACM_CUSTOM_DB_DSN = "<SMARTOFFERS_QA4_ACM_CUSTOM_DB_DSN>"
$env:SMARTOFFERS_QA4_ACM_CUSTOM_DB_USER = "<SMARTOFFERS_QA4_ACM_CUSTOM_DB_USER>"
$env:SMARTOFFERS_QA4_ACM_CUSTOM_DB_PASSWORD = "<SMARTOFFERS_QA4_ACM_CUSTOM_DB_PASSWORD>"
$env:SMARTOFFERS_ORACLE_CLIENT_LIB_DIR = "<SMARTOFFERS_ORACLE_CLIENT_LIB_DIR>"

# Optional QA1 endpoint, if a future local flow explicitly needs it.
# $env:SMARTOFFERS_QA1_API_URL = "<SMARTOFFERS_QA1_API_URL>"
