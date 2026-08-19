"""Import-only sanity check for every module - catches syntax/import
errors before a real (billed) run. Makes no network calls."""

import tools_fmp
import tools_yfinance
import notify
import orchestrator

print("tools_fmp: OK -", tools_fmp.fmp_server["name"])
print("tools_yfinance: OK -", tools_yfinance.yfinance_server["name"])
print("notify: OK -", notify.notify.__name__)
print("orchestrator: OK -", orchestrator.build_options.__name__)
print("orchestrator.ALLOWED_TOOLS:", orchestrator.ALLOWED_TOOLS)
