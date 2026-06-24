```text
QuotaLane simulation

┌────────────────────────┬──────────────────────────────┐
│ Job                    │ paragraph_summary_large_demo │
│ Work items             │ 9,800                        │
│ Estimated input tokens │ 6,779,991                    │
│ Lanes                  │ 4                            │
│ Batches planned        │ 31                           │
└────────────────────────┴──────────────────────────────┘

Dispatch window 1:
  gemini_key_1 -> batch_001 -> 224,775 tokens (succeeded)
  gemini_key_2 -> batch_002 -> 224,639 tokens (succeeded)
  gemini_key_3 -> batch_003 -> 224,334 tokens (succeeded)
  gemini_key_4 -> batch_004 -> 224,923 tokens (succeeded)

Dispatch window 2:
  gemini_key_1 -> batch_005 -> 224,914 tokens (succeeded)
  gemini_key_2 -> batch_006 -> 224,930 tokens (succeeded)
  gemini_key_3 -> batch_007 -> 224,579 tokens (succeeded)
  gemini_key_4 -> batch_008 -> 224,243 tokens (succeeded)

Dispatch window 3:
  gemini_key_1 -> batch_009 -> 224,670 tokens (succeeded)
  gemini_key_2 -> batch_010 -> 224,220 tokens (succeeded)
  gemini_key_3 -> batch_011 -> 224,607 tokens (succeeded)
  gemini_key_4 -> batch_012 -> 224,717 tokens (succeeded)

Dispatch window 4:
  gemini_key_1 -> batch_013 -> 224,827 tokens (succeeded)
  gemini_key_2 -> batch_014 -> 224,664 tokens (succeeded)
  gemini_key_3 -> batch_015 -> 224,540 tokens (succeeded)
  gemini_key_4 -> batch_016 -> 224,825 tokens (succeeded)

Dispatch window 5:
  gemini_key_1 -> batch_017 -> 224,552 tokens (succeeded)
  gemini_key_2 -> batch_018 -> 224,403 tokens (succeeded)
  gemini_key_3 -> batch_019 -> 224,710 tokens (succeeded)
  gemini_key_4 -> batch_020 -> 224,538 tokens (succeeded)

Dispatch window 6:
  gemini_key_1 -> batch_021 -> 224,836 tokens (succeeded)
  gemini_key_2 -> batch_022 -> 224,356 tokens (succeeded)
  gemini_key_3 -> batch_023 -> 224,729 tokens (succeeded)
  gemini_key_4 -> batch_024 -> 224,624 tokens (succeeded)

Dispatch window 7:
  gemini_key_1 -> batch_025 -> 224,373 tokens (succeeded)
  gemini_key_2 -> batch_026 -> 224,373 tokens (succeeded)
  gemini_key_3 -> batch_027 -> 224,500 tokens (succeeded)
  gemini_key_4 -> batch_028 -> 224,344 tokens (succeeded)

Dispatch window 8:
  gemini_key_1 -> batch_029 -> 224,686 tokens (succeeded)
  gemini_key_2 -> batch_030 -> 224,431 tokens (succeeded)
  gemini_key_3 -> batch_031 -> 42,129 tokens (succeeded)

Result:
  completed batches: 31
  failed batches: 0
  missing outputs: 0
  parallel lanes used: 4
  estimated dispatch windows: 8
  estimated elapsed time: ~8 minutes
  final status: completed
```
