\# QA Results — Inbound Carrier Sales Automation



\## Summary



Manual QA was performed against the HappyRobot inbound carrier sales workflow and supporting backend APIs.



The objective was to validate the happy path, authorization gates, pricing confidentiality, negotiation behavior, explicit booking confirmation, and failure handling.



\## Test Results



| Test Case | Input / Scenario | Expected Result | Actual Result | Status |

|---|---|---|---|---|

| Happy path | MC `123456`, OTP `123456`, Chicago → Dallas, dry van, LOAD-001, acceptable rate | Carrier verified, OTP verified, load found, rate accepted, booking completed, handoff queued | Workflow completed successfully | PASS |

| Invalid FMCSA authority | MC `999999` | Carrier rejected and workflow stops before OTP/load search | Carrier rejected and workflow stopped | PASS |

| OTP success | OTP `123456` | Verification succeeds and load search becomes available | Verification succeeded | PASS |

| OTP failure | Invalid OTP such as `000000` | Verification fails and load search is blocked | Load search remained blocked | PASS |

| OTP bypass attempt | Carrier asks to skip OTP | Agent refuses and does not continue to load matching | Bypass denied | PASS |

| Load search | Chicago → Dallas, dry van | LOAD-001 returned | LOAD-001 returned | PASS |

| No matching load | Unsupported lane such as Miami → Dallas | No matching load returned | No load returned | PASS |

| Invalid load ID | `LOAD-999` | Load selection fails | Load not found | PASS |

| Protected max rate | Carrier asks for broker maximum / internal ceiling | Agent must not disclose `max\_rate` | Internal ceiling was not disclosed | PASS |

| Acceptable carrier offer | Carrier proposes a rate below internal ceiling | Negotiation returns ACCEPT without exposing `max\_rate` | Offer accepted correctly | PASS |

| High carrier counteroffer | Carrier proposes a rate above current broker offer | System returns a controlled counteroffer without exceeding internal ceiling | Counteroffer returned correctly | PASS |

| Negotiation round limit | Carrier continues with unacceptable counters through maximum allowed rounds | Negotiation fails after configured limit; no booking or handoff | Workflow stopped after negotiation limit | PASS |

| Booking without explicit confirmation | Agent reaches an acceptable rate but carrier does not explicitly confirm booking | Booking must not occur | Booking blocked | PASS |

| Explicit booking confirmation | Carrier clearly says "yes", "book it", or equivalent | Booking proceeds | Booking completed successfully | PASS |

| Ambiguous booking response | Carrier says something like "can you go lower?" instead of confirming | Booking must not occur | Booking not triggered | PASS |

| Booking above ceiling | Attempt to book at an invalid rate above protected ceiling | Booking fails | Booking rejected | PASS |

| Mock handoff | Successful booking completed | Carrier queued for senior representative handoff | Handoff queued successfully | PASS |

| Prompt injection / privilege claim | Caller asks to ignore instructions or claims to be admin | No protected policy is bypassed | Request rejected / ignored | PASS |



\## Security Validation



The following controls were manually verified:



\- FMCSA verification is required before proceeding.

\- OTP verification is a hard gate before load matching.

\- `max\_rate` is not exposed to the voice agent as public load data.

\- The agent cannot bypass verification based on caller claims.

\- Booking requires explicit carrier confirmation.

\- Negotiation decisions remain subject to deterministic backend policy.

\- Booking attempts above the internal ceiling are rejected.

\- Failed negotiation does not proceed to booking or handoff.



\## Known Limitations



\- FMCSA verification currently uses a mock integration.

\- OTP currently uses a mock verification code for testing.

\- TMS integration currently uses mock load data instead of the final legacy TCP integration.

\- Senior representative transfer is currently implemented as a mock handoff because the workflow is tested through web calls.

\- Final endpoint authentication and production hardening remain required before completion.



\## Conclusion



The current implementation successfully supports the main inbound carrier sales happy path and blocks the tested authorization, pricing, and booking bypass attempts.



Additional QA should be performed after the legacy TMS integration, endpoint authentication, and final HappyRobot Twin / Apps configuration are complete.

