-- CSAT Callback Script (Triggered on Hangup)
local caller = (session and session:getVariable("caller_id_number")) or (env and env:getHeader("Caller-Caller-ID-Number")) or "Unknown"
local destination = (session and session:getVariable("destination_number")) or (env and env:getHeader("Caller-Destination-Number")) or "Unknown"
local answer_stamp = (session and session:getVariable("real_answered_at")) or (session and session:getVariable("answer_stamp")) or (env and env:getHeader("variable_answer_stamp")) or "N/A"

-- التأكد من أن المكالمة الأصلية تمت إجابتها وليست مكالمة تقييم لتجنب الدوران اللانهائي
if answer_stamp ~= "N/A" and answer_stamp ~= "" and caller ~= "Unknown" and destination ~= "9999" then
    local api = freeswitch.API()
    -- الاتصال بالعميل وتوجيهه لإكستنشن التقييم 9999
    local originate_cmd = string.format("bgapi originate {ignore_early_media=true,absolute_codec_string=PCMA,PCMU,origination_caller_id_name='CSAT'}user/%s 9999 xml default", caller)
    api:executeString(originate_cmd)
end
