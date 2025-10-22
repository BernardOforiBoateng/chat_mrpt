🔬 Comprehensive Vision Test with Debugging...

🚀 Deploying to Instance 1 (3.21.167.170)...
  - Copying debugged universal_viz_explainer.py...
  - Copying container.py...
  - Copying llm_adapter.py...

🧪 Running comprehensive test on Instance 1...

A newer release of "Amazon Linux" is available.
  Version 2023.8.20250707:
  Version 2023.8.20250715:
  Version 2023.8.20250721:
  Version 2023.8.20250808:
  Version 2023.8.20250818:
  Version 2023.8.20250908:
  Version 2023.8.20250915:
Run "/usr/bin/dnf check-release-update" for full release and version update info
   ,     #_
   ~\_  ####_        Amazon Linux 2023
  ~~  \_#####\
  ~~     \###|
  ~~       \#/ ___   https://aws.amazon.com/linux/amazon-linux-2023
   ~~       V~' '->
    ~~~         /
      ~~._.   _/
         _/ _/
       _/m/'
  - Clearing Python cache...
  - Restarting service...
  - Running test...
INFO [app.core.llm_adapter] LLM Adapter initialized: backend=openai, model=gpt-4o
INFO [app.services.universal_viz_explainer] Found valid cached explanation (age: 1627s)
INFO [app.services.universal_viz_explainer] Using cached explanation for: tpr_map
INFO [app] ✅ Redis session store initialized at chatmrpt-redis-staging.1b3pmt.0001.use2.cache.amazonaws.com:6379
DEBUG [app.services.container] Registered service: interaction_logger (singleton: True)
DEBUG [app.services.container] Registered service: llm_manager (singleton: True)
DEBUG [app.services.container] Registered service: data_service (singleton: True)
DEBUG [app.services.container] Registered service: analysis_service (singleton: True)
DEBUG [app.services.container] Registered service: visualization_service (singleton: True)
DEBUG [app.services.container] Registered service: report_service (singleton: True)
DEBUG [app.services.container] Registered service: request_interpreter (singleton: True)
INFO [app.services.container] 🚀 Starting eager initialization of core services...
INFO [app.interaction] Interaction package v1.0.0 initialized with 39 exported functions
INFO [app.interaction.core] Interaction database initialized at /home/ec2-user/ChatMRPT/instance/interactions.db
DEBUG [app.services.container] Created service instance: interaction_logger
INFO [app.services.container] ✅ interaction_logger initialized in 0.01s
INFO [app.services.container] 🔍 DEBUG: USE_VLLM = False (from env: None)
INFO [app.services.container] 🔍 DEBUG: USE_OLLAMA = False (from env: None)
INFO [app.services.container] ☁️ Using OpenAI for cloud inference
INFO [app.core.llm_adapter] LLM Adapter initialized: backend=openai, model=gpt-4o
DEBUG [openai._base_client] Request options: {'method': 'post', 'url': '/chat/completions', 'files': None, 'idempotency_key': 'stainless-python-retry-91524f1a-f922-41ba-bb4b-17da796b3b8f', 'json_data': {'messages': [{'role': 'user', 'content': '<|im_start|>system\nYou are ChatMRPT, a helpful assistant for malaria risk analysis. Provide concise, direct responses without showing internal reasoning.<|im_end|>\n<|im_start|>user\nHello<|im_end|>\n<|im_start|>assistant\n'}], 'model': 'gpt-4o', 'max_tokens': 10, 'temperature': 0.1}}
DEBUG [openai._base_client] Sending HTTP Request: POST https://api.openai.com/v1/chat/completions
DEBUG [httpcore.connection] connect_tcp.started host='api.openai.com' port=443 local_address=None timeout=5.0 socket_options=None
DEBUG [httpcore.connection] connect_tcp.complete return_value=<httpcore._backends.sync.SyncStream object at 0x7f64d8daf550>
DEBUG [httpcore.connection] start_tls.started ssl_context=<ssl.SSLContext object at 0x7f64d9210440> server_hostname='api.openai.com' timeout=5.0
DEBUG [httpcore.connection] start_tls.complete return_value=<httpcore._backends.sync.SyncStream object at 0x7f64d8daf610>
DEBUG [httpcore.http11] send_request_headers.started request=<Request [b'POST']>
DEBUG [httpcore.http11] send_request_headers.complete
DEBUG [httpcore.http11] send_request_body.started request=<Request [b'POST']>
DEBUG [httpcore.http11] send_request_body.complete
DEBUG [httpcore.http11] receive_response_headers.started request=<Request [b'POST']>
DEBUG [httpcore.http11] receive_response_headers.complete return_value=(b'HTTP/1.1', 200, b'OK', [(b'Date', b'Fri, 19 Sep 2025 20:08:16 GMT'), (b'Content-Type', b'application/json'), (b'Transfer-Encoding', b'chunked'), (b'Connection', b'keep-alive'), (b'access-control-expose-headers', b'X-Request-ID'), (b'openai-organization', b'urban-malaria-lab'), (b'openai-processing-ms', b'411'), (b'openai-project', b'proj_PWHKJkkYCgtBisYo4OfhgZoI'), (b'openai-version', b'2020-10-01'), (b'x-envoy-upstream-service-time', b'526'), (b'x-ratelimit-limit-requests', b'5000'), (b'x-ratelimit-limit-tokens', b'800000'), (b'x-ratelimit-remaining-requests', b'4999'), (b'x-ratelimit-remaining-tokens', b'799943'), (b'x-ratelimit-reset-requests', b'12ms'), (b'x-ratelimit-reset-tokens', b'4ms'), (b'x-request-id', b'req_bb87ab1edceb470b8846e7bc29d34fb9'), (b'x-openai-proxy-wasm', b'v0.1'), (b'cf-cache-status', b'DYNAMIC'), (b'Set-Cookie', b'__cf_bm=nWmFBub06WW3o.v6gO.7v0ar7ogcq0FLjOeUmeaWzgQ-1758312496-1.0.1.1-AwlR7ifz3A6OhZMpjMKBmEzdtdApkbqNyCLyhfU7oyKtfNaY5WMKGGLV746DhON239NnIhc4Nc35C8F8iOA999DB_osyFYCsJssf1CbITV0; path=/; expires=Fri, 19-Sep-25 20:38:16 GMT; domain=.api.openai.com; HttpOnly; Secure; SameSite=None'), (b'Strict-Transport-Security', b'max-age=31536000; includeSubDomains; preload'), (b'X-Content-Type-Options', b'nosniff'), (b'Set-Cookie', b'_cfuvid=MJIJqf2_0JikQdg313eFfIGbIyhYz4Erkb0oIu0ERA8-1758312496605-0.0.1.1-604800000; path=/; domain=.api.openai.com; HttpOnly; Secure; SameSite=None'), (b'Server', b'cloudflare'), (b'CF-RAY', b'981bb6cc1ed1258a-CMH'), (b'Content-Encoding', b'gzip'), (b'alt-svc', b'h3=":443"; ma=86400')])
INFO [httpx] HTTP Request: POST https://api.openai.com/v1/chat/completions "HTTP/1.1 200 OK"
DEBUG [httpcore.http11] receive_response_body.started request=<Request [b'POST']>
DEBUG [httpcore.http11] receive_response_body.complete
DEBUG [httpcore.http11] response_closed.started
DEBUG [httpcore.http11] response_closed.complete
DEBUG [openai._base_client] HTTP Response: POST https://api.openai.com/v1/chat/completions "200 OK" Headers([('date', 'Fri, 19 Sep 2025 20:08:16 GMT'), ('content-type', 'application/json'), ('transfer-encoding', 'chunked'), ('connection', 'keep-alive'), ('access-control-expose-headers', 'X-Request-ID'), ('openai-organization', 'urban-malaria-lab'), ('openai-processing-ms', '411'), ('openai-project', 'proj_PWHKJkkYCgtBisYo4OfhgZoI'), ('openai-version', '2020-10-01'), ('x-envoy-upstream-service-time', '526'), ('x-ratelimit-limit-requests', '5000'), ('x-ratelimit-limit-tokens', '800000'), ('x-ratelimit-remaining-requests', '4999'), ('x-ratelimit-remaining-tokens', '799943'), ('x-ratelimit-reset-requests', '12ms'), ('x-ratelimit-reset-tokens', '4ms'), ('x-request-id', 'req_bb87ab1edceb470b8846e7bc29d34fb9'), ('x-openai-proxy-wasm', 'v0.1'), ('cf-cache-status', 'DYNAMIC'), ('set-cookie', '__cf_bm=nWmFBub06WW3o.v6gO.7v0ar7ogcq0FLjOeUmeaWzgQ-1758312496-1.0.1.1-AwlR7ifz3A6OhZMpjMKBmEzdtdApkbqNyCLyhfU7oyKtfNaY5WMKGGLV746DhON239NnIhc4Nc35C8F8iOA999DB_osyFYCsJssf1CbITV0; path=/; expires=Fri, 19-Sep-25 20:38:16 GMT; domain=.api.openai.com; HttpOnly; Secure; SameSite=None'), ('strict-transport-security', 'max-age=31536000; includeSubDomains; preload'), ('x-content-type-options', 'nosniff'), ('set-cookie', '_cfuvid=MJIJqf2_0JikQdg313eFfIGbIyhYz4Erkb0oIu0ERA8-1758312496605-0.0.1.1-604800000; path=/; domain=.api.openai.com; HttpOnly; Secure; SameSite=None'), ('server', 'cloudflare'), ('cf-ray', '981bb6cc1ed1258a-CMH'), ('content-encoding', 'gzip'), ('alt-svc', 'h3=":443"; ma=86400')])
DEBUG [openai._base_client] request_id: req_bb87ab1edceb470b8846e7bc29d34fb9
INFO [app.services.container] ✅ LLM backend verified: openai with gpt-4o
DEBUG [app.services.container] Created service instance: llm_manager
INFO [app.services.container] ✅ llm_manager initialized in 1.03s
DEBUG [app.services.container] Created service instance: data_service
INFO [app.services.container] ✅ data_service initialized in 0.00s
DEBUG [httpcore.connection] close.started
DEBUG [httpcore.connection] close.complete
DEBUG [app.services.container] Created service instance: analysis_service
INFO [app.services.container] ✅ analysis_service initialized in 0.98s
DEBUG [app.services.container] Created service instance: visualization_service
INFO [app.services.container] ✅ visualization_service initialized in 0.14s
DEBUG [app.services.container] Created service instance: report_service
INFO [app.services.container] ✅ report_service initialized in 0.00s
ERROR [app.core.arena_integration_patch] Failed to patch RequestInterpreter: cannot import name 'RequestInterpreter' from partially initialized module 'app.core.request_interpreter' (most likely due to a circular import) (/home/ec2-user/ChatMRPT/app/core/request_interpreter.py)
INFO [app.core.request_interpreter] Arena integration components loaded successfully
INFO [app.core.interpreter_migration] Creating legacy RequestInterpreter
DEBUG [app.core.request_interpreter] Memory service not available: No module named 'app.services.memory_service'
INFO [app.core.request_interpreter] Registering tools - py-sidebot pattern
INFO [app.core.request_interpreter] Registered 12 tools
DEBUG [app.services.container] Created service instance: request_interpreter
INFO [app.services.container] ✅ request_interpreter initialized in 0.00s
INFO [app.services.container] 🎯 Eager initialization complete - services ready for instant responses!
INFO [app.services.container] Service container initialized with core services
INFO [app] 🚀 Development mode - Using in-memory conversation tracking
DEBUG [rasterio.session] Could not import boto3, continuing with reduced functionality.
DEBUG [rasterio.env] GDAL data found in package: path='/home/ec2-user/chatmrpt_env/lib64/python3.11/site-packages/rasterio/gdal_data'.
DEBUG [rasterio.env] PROJ data found in package: path='/home/ec2-user/chatmrpt_env/lib64/python3.11/site-packages/rasterio/proj_data'.
INFO [app.survey] ✅ Survey database already has 84 questions
INFO [app.web.routes] ✅ Export routes registered
INFO [app.web.routes] ✅ Session routes registered
INFO [app.web.routes] ✅ Arena routes registered
INFO [app.web.routes] ✅ Survey routes registered
INFO [app.web.routes] ✅ Data Analysis V3 routes registered
INFO [app.interaction.core] Interaction database initialized at instance/interactions.db
INFO [app.core.arena_manager] ✅ Connected to Redis at chatmrpt-redis-staging.1b3pmt.0001.use2.cache.amazonaws.com:6379
INFO [app.core.arena_manager] Loaded arena stats from disk
INFO [app.core.arena_manager] Arena Manager initialized with 3 models
INFO [app.core.arena_manager] Redis storage: Connected
INFO [app.web.routes.arena_routes] Arena system initialized
INFO [app] ✅ Arena system initialized successfully
INFO [app] ChatMRPT v3.0 - Modern Architecture Initialized
INFO [app] Configuration: DevelopmentConfig
INFO [app] Services: Available
DEBUG [app] Request: POST http://localhost/explain_visualization
INFO [app.services.universal_viz_explainer] Found valid cached explanation (age: 1614s)
INFO [app.services.universal_viz_explainer] Using cached explanation for: tpr_map
INFO [app.core.decorators] explain_visualization executed in 0.00 seconds
======================================================================
COMPREHENSIVE VISION TEST WITH DEBUGGING
======================================================================

======================================================================
TEST 1: Direct Service Test
======================================================================

1. Creating LLMAdapter...
   ✓ LLMAdapter created
   ✓ Backend: openai
   ✓ Has generate_with_image: True

2. Creating UniversalVisualizationExplainer...
   ✓ Explainer created

3. Calling explain_visualization...
   Input file: /tmp/tmp33s4umc7.html

4. Direct Test Results:
----------------------------------------------------------------------
✅ SUCCESS: Found test data in explanation: ['92%', 'Region X', 'URGENT', '67%', 'Region Y']
   Vision API is working correctly!

Explanation preview (first 400 chars):
1. **Most Important Pattern or Finding:**
   The visualization highlights Region X with a Test Positivity Rate (TPR) of 92%, marked as "URGENT." This indicates a critical level of malaria transmission needing immediate attention.

2. **Standout Areas or Data Points:**
   - **Region X:** With the highest TPR of 92%, this area is in urgent need of intervention.
   - **Region Y:** Has a high TPR of 6

======================================================================
TEST 2: Flask Route Test
======================================================================
[DEV] ChatMRPT Development Mode
[DEV] Instance folder: /home/ec2-user/ChatMRPT/instance
[DEV] OpenAI API Key: Set
[DEV] Debug Mode: True

1. Testing /explain_visualization endpoint...
   Response status: 200
   ✅ Flask SUCCESS: Found indicators: ['92%', 'Region X', 'URGENT', '67%', 'Region Y']

   Flask explanation preview:
   1. **Most Important Pattern or Finding:**
   - The most critical pattern in this visualization is the extremely high Test Positivity Rate (TPR) in Region X, marked as "URGENT" with a TPR of 92%. This indicates a severe malaria risk.

2. **Specific Areas, Values, or Data Points:**
   - **Region X**: ...

======================================================================
TEST 3: Services Container Test
======================================================================

1. Getting LLM from services container...
   Type: LLMManagerWrapper
   Has generate_with_image: True
   Adapter type: LLMAdapter
   Adapter has method: True

======================================================================
SUMMARY
======================================================================
Check the DEBUG log messages above to see:
1. What type of LLM manager is being used
2. Whether generate_with_image is available
3. If image capture is successful
4. What the vision API returns

  - Checking service logs for DEBUG messages...
✅ Done testing Instance 1

📊 Test Complete!

Look for these indicators of success:
✅ 'Found test data in explanation' - Vision is working
❌ 'FALLBACK: Still getting generic' - Vision not working

Check the DEBUG messages to see exactly what's happening!
