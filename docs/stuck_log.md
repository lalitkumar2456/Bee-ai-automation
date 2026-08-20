# Stuck Log

Record of real troubleshooting performed during the assignment.

## Entry 1: Audio loudness extraction

- **Problem:** Initial audio metadata extraction returned duration, sample rate, and bitrate, but loudness was not calculated.
- **Evidence:** Earlier audio inspection returned `loudness_db: None` with a note that loudness required FFmpeg EBU R128 analysis.
- **What I tried:** Updated `app/audio.py` to use the local/bundled FFmpeg executable and added an EBU R128 loudness analysis pass.
- **Why it failed or was rejected:** The original implementation did not perform integrated loudness analysis.
- **Resolution and reasoning:** Added FFmpeg `ebur128` analysis and validation. A test M4A file subsequently returned `duration_seconds: 10.69`, `sample_rate_hz: 48000`, `bitrate_kbps: 205.0`, and `loudness_db: -17.4`.
- **AI/search used:** AI assistance during implementation and debugging.

## Entry 2: Docker/n8n connection

- **Problem:** Docker commands initially failed to connect to the Docker API.
- **Evidence:** Docker reported that `dockerDesktopLinuxEngine` could not be found and that the daemon was not running.
- **What I tried:** Checked the Docker state and attempted to run the n8n container.
- **Why it failed or was rejected:** Docker Desktop's Linux engine was not running.
- **Resolution and reasoning:** Started Docker Desktop and confirmed the n8n environment was available. n8n was then accessible locally.
- **AI/search used:** AI assistance during troubleshooting.

## Entry 3: n8n webhook registration

- **Problem:** Calling the n8n test webhook returned a 404 saying the webhook was not registered.
- **Evidence:** n8n returned: `The requested webhook "consultbae-classify" is not registered` and instructed that the Execute workflow button must be used in test mode.
- **What I tried:** Sent a POST request to `/webhook-test/consultbae-classify`.
- **Why it failed or was rejected:** The workflow had not been put into test execution mode, so the temporary test webhook was not registered.
- **Resolution and reasoning:** Clicked Execute workflow in n8n and then sent the POST request again. The webhook accepted the request successfully.
- **AI/search used:** AI assistance during troubleshooting.

## Entry 4: Dynamic person classification in n8n

- **Problem:** The n8n workflow needed to classify whichever person ID was supplied to the webhook rather than a fixed person.
- **Evidence:** A hard-coded URL such as `/people/12/classification-input` would only retrieve person 12.
- **What I tried:** Tested the FastAPI classification-input endpoint and then connected it to the n8n webhook payload.
- **Why it failed or was rejected:** A hard-coded person ID would not satisfy a reusable automation workflow.
- **Resolution and reasoning:** Changed the n8n HTTP Request URL to use the webhook payload dynamically:

  `http://host.docker.internal:8010/people/{{$json.body.person_id}}/classification-input`

  The workflow then successfully retrieved and updated the supplied person's classification.
- **AI/search used:** AI assistance during workflow design and debugging.

## Entry 5: PowerShell SQLite quoting

- **Problem:** Resetting the classification using a one-line PowerShell `python -c` command repeatedly produced Python syntax errors.
- **Evidence:** PowerShell/Python returned errors including `SyntaxError: unterminated string literal` and `SyntaxError: '(' was never closed`.
- **What I tried:** Tried different combinations of PowerShell and Python quoting.
- **Why it failed or was rejected:** Nested single and double quotes were being interpreted by PowerShell before reaching Python.
- **Resolution and reasoning:** Opened the Python interpreter directly, executed the SQLite statements interactively, committed the change, and verified that person 12 returned to `classification = None` and `classification_status = pending`.
- **AI/search used:** AI assistance during troubleshooting.