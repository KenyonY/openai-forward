wrk.method = "POST"
wrk.body   = '{"stream":"false"}'
-- wrk.body   = '{"stream":"true"}'
wrk.headers["Content-Type"] = "application/json"

-- wrk.timeout = 20000 -- in milliseconds
