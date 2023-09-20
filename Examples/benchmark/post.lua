wrk.method = "POST"
wrk.headers["Content-Type"] = "application/json"
-- wrk.body = '{"stream": false}'
wrk.body   = '{"stream":true}'

-- wrk.timeout = 20000 -- in milliseconds

-- request = function()
--     return wrk.format(nil, nil, nil, wrk.body)
-- end