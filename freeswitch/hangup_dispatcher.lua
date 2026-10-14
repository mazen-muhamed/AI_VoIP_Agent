-- Dispatcher script to handle multiple hangup hooks independently
-- Uses pcall (protected call) so if one script fails or is missing, the other still executes

-- Execute summary logging script
pcall(function()
    dofile("/usr/local/freeswitch/scripts/log_task_summary.lua")
end)

-- Execute CSAT callback script
pcall(function()
    dofile("/usr/local/freeswitch/scripts/csat_callback.lua")
end)
