-- 1. Call Details & Metadata
local uuid = (session and session:getVariable("uuid")) or (env and env:getHeader("Unique-ID")) or "N/A"
local direction = (session and session:getVariable("direction")) or (env and env:getHeader("Call-Direction")) or "inbound"
local caller = (session and session:getVariable("caller_id_number")) or (env and env:getHeader("Caller-Caller-ID-Number")) or "Unknown"
local destination = (session and session:getVariable("destination_number")) or (env and env:getHeader("Caller-Destination-Number")) or "Unknown"

local start_stamp = (session and session:getVariable("start_stamp")) or (env and env:getHeader("variable_start_stamp")) or "N/A"
local answer_stamp = (session and session:getVariable("real_answered_at")) or (session and session:getVariable("answer_stamp")) or (env and env:getHeader("variable_answer_stamp")) or "N/A"
local end_stamp = (session and session:getVariable("end_stamp")) or (env and env:getHeader("variable_end_stamp")) or "N/A"
local hangup_cause = (session and session:getVariable("hangup_cause")) or (env and env:getHeader("Hangup-Cause")) or "NORMAL_CLEARING"

-- 2. Call Routing & Transfer Status
local ai_resolved = (session and session:getVariable("ai_resolved")) or (env and env:getHeader("variable_ai_resolved")) or "false"
local transferred_to_human = (session and session:getVariable("transferred_to_human")) or (env and env:getHeader("variable_transferred_to_human")) or "false"
local transfer_reason = (session and session:getVariable("transfer_reason")) or (env and env:getHeader("variable_transfer_reason")) or "none"

local call_status = "COMPLETED"
if answer_stamp == "N/A" or answer_stamp == "" then
    call_status = "ABANDONED"
elseif hangup_cause ~= "NORMAL_CLEARING" then
    call_status = "FAILED"
end

-- Formatted Console Output
freeswitch.consoleLog("INFO", string.format(
    "\n+-----------------------------------------------------------------+" ..
    "\n| CALL SUMMARY REPORT                                             |" ..
    "\n+-----------------------------------------------------------------+" ..
    "\n  UUID         : %s" ..
    "\n  Direction    : %s" ..
    "\n  Routing      : %s -> %s" ..
    "\n  Timestamps   : Start [%s] | Answer [%s] | End [%s]" ..
    "\n  Discretion   : Status [%s] | Hangup Cause [%s]" ..
    "\n+-----------------------------------------------------------------+" ..
    "\n  AI Resolved  : %s" ..
    "\n  Transferred  : %s (Reason: %s)" ..
    "\n+-----------------------------------------------------------------+\n",
    tostring(uuid),
    tostring(direction),
    tostring(caller), tostring(destination),
    tostring(start_stamp), tostring(answer_stamp), tostring(end_stamp),
    tostring(call_status), tostring(hangup_cause),
    tostring(ai_resolved),
    tostring(transferred_to_human), tostring(transfer_reason)
))
