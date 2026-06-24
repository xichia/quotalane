# Demo transcript

```bash
$ quotalane simulate examples/paragraph_summary_large_job.yaml --reset --no-windows

QuotaLane simulation

Job: paragraph_summary_large_demo
Work items: 9,800
Estimated input tokens: 6,779,991
Lanes: 4
Batches planned: 31

Result:
  completed batches: 31
  failed batches: 0
  missing outputs: 0
  parallel lanes used: 4
  estimated dispatch windows: 8
  estimated elapsed time: ~8 minutes
  final status: completed
```

The important portfolio point is the parallel lane usage: with four configured lanes, QuotaLane dispatches four large token batches per virtual minute instead of processing them serially through one key.
