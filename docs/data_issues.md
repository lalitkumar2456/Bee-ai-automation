# Data-quality report

This project preserves raw source values in `person_sources` and applies transformations only while ingesting.

| Issue | Handling |
| --- | --- |
| Duplicate people within and across sources | Exact normalized email first, then exact normalized phone. `name + city` is used only when it produces one candidate. |
| Phone formats such as `+91-9000000131` and `919000000131` | Strip non-digits and retain the last 10 digits. |
| City casing and aliases (`PUNE`, `Gurgaon`, `Bangalore`) | Case-normalize and map known aliases to Pune, Gurugram, and Bengaluru. |
| Empty Source 2 row | Skip entirely blank records. |
| Repeated Source 3 header in data | Skip a row where the name value equals the header label. |
| Shifted Source 2 Isha Chopra row | Detect skills in the email field plus an email in the name field, then reconstruct values by pattern. |
| Mixed CTC units | Values below 100 are interpreted as LPA and converted to annual INR. This is an inference retained in documentation. |
| Mixed date formats / future dates | Parse known formats to ISO dates. A source future date is preserved rather than silently changed. |
| Same name, conflicting identifiers | Do not auto-merge. Add the record to `review_queue` when a name/city lookup has multiple candidates. |

## Matching policy

Precision is preferred over aggressive deduplication: a false merge can corrupt a person record. Each ingestion also keeps the source record, original identifiers, and match method for auditability.
