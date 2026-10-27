# Test Plan

1. Start application and verify dashboard loads.
2. Click Collect Local Metrics and verify one server appears.
3. Run scripts/simulate_servers.py and verify multiple servers appear.
4. Send CPU > 90 and verify CRITICAL status.
5. Send a value between 80 and 89.99 and verify WARNING.
6. Send all values below 80 and verify HEALTHY.
7. Verify alerts appear in Recent Alerts.
8. Stop/restart application and verify SQLite data remains.
9. Run linux_agent.py on a Linux test VM and verify remote ingestion.
10. Verify invalid API payload returns HTTP 400.
