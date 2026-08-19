# Verified data-quality handling

This report is based on the committed CSV files in `data/` and the behavior of `etl/ingest.py`. CSV line numbers include the header row. Reproduce ingestion with `python -m etl.ingest`.

## Identity, contact, and location fields

| Verified source condition | Why it matters | Current handling | Preservation / limitation |
| --- | --- | --- | --- |
| `R. Verma` (Source 1 line 25) and `Rohit Verma` (line 31) have the same email and phone. | A name-only rule would miss the abbreviated duplicate. | The record matches by normalized exact email. | `person_sources` keeps both raw names, emails, and phones. The canonical name remains the first inserted form (`R Verma`); initials are not expanded. |
| `Nikhil Chopra` appears at Source 1 lines 27 and 37 with the same normalized phone but different emails. | Email-only matching would create two people. | The second record matches by exact normalized phone. | Both source records and original emails are retained. The first email remains canonical; no preferred-email rule exists. |
| Phones use `+91-`, `91`, leading `0`, dashes, and plain ten-digit forms (for example Source 1 line 2 and Source 3 line 5). | Direct comparison fails across formats. | `normalize_phone` strips non-digits and keeps the final ten digits. | The source phone string is retained in `person_sources.raw_phone`. |
| Email casing varies (for example Source 2 lines 7 and 20). | Case-sensitive comparison would miss the same address. | `normalize_email` trims and lowercases values containing `@`. | The supplied email string is retained in `person_sources.raw_email`. |
| Cities vary by case, whitespace, and aliases: `GURGAON`, `gurugram `, `Bangalore`, `new delhi`, and `NOIDA`. | Equivalent locations would not compare consistently. | `normalize_city` trims/case-normalizes and maps Gurgaon/Gurugram, Bangalore/Bengaluru, and New Delhi/Delhi aliases. | Only normalized city is stored; raw city is not separately retained. |
| `Arjun Mehta` occurs with phone `9000000131` (Source 1 line 20 / Source 3 line 5), a different phone `9000000272` (Source 3 line 28), and a third email-only record (Source 2 line 18), all in Noida. | Same name and city do not prove identity. | Exact identifiers run first; otherwise the current last-resort rule matches a uniquely found `name + city`. | **Known limitation:** this produces one `Arjun Mehta` person with four source rows. The fallback can over-merge plausible distinct people. |
| An incoming email and phone can resolve to different existing people. | Choosing one identifier would silently corrupt an identity. | `find_match` returns `conflicting_exact_identifiers`; ingestion writes the row to `review_queue`. | The supplied CSVs do not trigger this case, but an automated regression test covers it. |

## Structural and field-format issues

| Verified source condition | Why it matters | Current handling | Preservation / limitation |
| --- | --- | --- | --- |
| Source 2 line 12 is blank. | It is not a person record. | Rows with no nonblank values are skipped. | The raw CSV is unchanged. |
| Source 2 line 20 is shifted: skills are in `email_id`, email is in `worker_name`, and later values are offset. | Normal mapping would store invalid fields. | A field-pattern check reconstructs name, email, city, and skills. | Reconstructed identity fields are stored; rate/status are not persisted. |
| Source 3 line 16 repeats the header row as data. | It would create a fake person named `Name`. | A row whose source name equals the header label is skipped. | The raw CSV is unchanged. |
| Source 1 dates use ISO, `DD-MM-YYYY`, `MM/DD/YYYY`, and textual month formats (for example lines 2, 5, 8, and 9). | Date comparison and sorting would be inconsistent. | `normalize_date` parses supported formats to `YYYY-MM-DD`. | Invalid dates become `NULL`; none occur in this dataset. |
| Source 1 mixes values below 100 in `Current CTC` (for example `4.2` on line 6) with values such as `417964` (line 2). | The column appears to mix LPA and annual INR. | `normalize_ctc` treats values below 100 as LPA and multiplies by 100,000. | This is an explicit inference; raw CTC is not separately retained. |
| Source 1 has future application dates relative to 2026-08-19, including 21-08-2026 (line 14) and 22-08-2026 (line 17). | Future application dates may require business validation. | The parser normalizes and stores them. | They are neither flagged nor rejected; a validation flag is a future improvement. |
| Source 2 rates use incompatible units (`1415/hr`, `15k/month`); Source 2 status and Source 3 verification values also vary (`Y`, `yes`, `No`, `N`). | They cannot safely be compared without a business rule. | They are not mapped into the canonical schema. | They are not retained in `person_sources`; dedicated fields are a future enhancement. |

## Matching policy and audit trail

The matching order is exact normalized email, exact normalized phone, then name plus city only when it yields one candidate. Exact-identifier conflicts are sent to `review_queue`. `person_sources` records source filename, source line number, raw name/email/phone, and the match method. The limitations above identify where manual review or a stricter policy is still needed.
