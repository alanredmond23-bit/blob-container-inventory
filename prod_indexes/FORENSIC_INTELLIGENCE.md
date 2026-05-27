# Forensic Intelligence Report

**Generated:** 2026-05-26T11:54:50.847811+00:00
**Disks reviewed:** 11
**Total flags:** 72
**Case:** US v. Redmond, 5:24-cr-00376, EDPA

---

## Disk Summary

| Disk | Files | GB | Archives | Compression Save |
|---|---:|---:|---:|---:|
| `T7` | 4 | 322.0 | 1 | 0.0% |
| `T7` | 4 | 322.0 | 1 | 0.0% |
| `blacksand` | 568 | 1000.0 | 1 | 25.0% |
| `blacksand` | 568 | 1000.0 | 1 | 25.0% |
| `blacksand` | 568 | 1000.0 | 1 | 25.0% |
| `creamsam` | 846,733 | 412.5 | 1 | 6.5% |
| `creamsam` | 846,733 | 412.5 | 1 | 6.5% |
| `creamsam` | 846,738 | 412.5 | 1 | 6.6% |
| `usbmemorex` | 149,791 | 20.9 | 2 | 68.3% |
| `usbmemorex` | 149,791 | 20.9 | 2 | 68.3% |
| `usbmemorex` | 149,801 | 20.9 | 3 | 68.3% |

## HIGH (6)

### EXTENSION_ANOMALY
**Disk:** `blacksand`  
**ext:** `.exe`  
**count:** `1`  
**bytes:** `5497624`  

> executable in discovery — should not exist unless produced as evidence

### EXTENSION_ANOMALY
**Disk:** `blacksand`  
**ext:** `.exe`  
**count:** `1`  
**bytes:** `5497624`  

> executable in discovery — should not exist unless produced as evidence

### EXTENSION_ANOMALY
**Disk:** `blacksand`  
**ext:** `.exe`  
**count:** `1`  
**bytes:** `5497624`  

> executable in discovery — should not exist unless produced as evidence

### EXTENSION_ANOMALY
**Disk:** `creamsam`  
**ext:** `.exe`  
**count:** `1`  
**bytes:** `5468400`  

> executable in discovery — should not exist unless produced as evidence

### EXTENSION_ANOMALY
**Disk:** `creamsam`  
**ext:** `.exe`  
**count:** `1`  
**bytes:** `5468400`  

> executable in discovery — should not exist unless produced as evidence

### EXTENSION_ANOMALY
**Disk:** `creamsam`  
**ext:** `.exe`  
**count:** `1`  
**bytes:** `5468400`  

> executable in discovery — should not exist unless produced as evidence

## MEDIUM (55)

### LARGE_FILE
**Disk:** `T7`  
**path:** `/Volumes/T7/REDMOND008836.zip`  
**size_gb:** `322.03`  
**ext:** `.zip`  

> File > 1GB warrants manual inspection.

### ACTOR_IN_PATH
**Disk:** `T7`  
**actor:** `redmond`  
**example_paths:** `['/Volumes/T7/REDMOND008836.zip']`  

> Key actor "redmond" appears in file/directory names. Review for relevance to carrier defense or Brady material.

### LARGE_FILE
**Disk:** `T7`  
**path:** `/Volumes/T7/REDMOND008836.zip`  
**size_gb:** `322.03`  
**ext:** `.zip`  

> File > 1GB warrants manual inspection.

### ACTOR_IN_PATH
**Disk:** `T7`  
**actor:** `redmond`  
**example_paths:** `['/Volumes/T7/REDMOND008836.zip']`  

> Key actor "redmond" appears in file/directory names. Review for relevance to carrier defense or Brady material.

### EXTENSION_ANOMALY
**Disk:** `blacksand`  
**ext:** `.dll`  
**count:** `1`  
**bytes:** `781888`  

> Windows library — investigate purpose

### MULTI_VOLUME_ARCHIVES
**Disk:** `blacksand`  
**count:** `1`  
**groups:** `{'encrypted.dsk': 366}`  

> Large spanned archives — may contain comprehensive data dumps. Central directory read needed to enumerate inner entries.

### LARGE_FILE
**Disk:** `blacksand`  
**path:** `/Volumes/blacksand/McAfee EERM/encrypted.dsk.99`  
**size_gb:** `2.15`  
**ext:** `.99`  

> File > 1GB warrants manual inspection.

### LARGE_FILE
**Disk:** `blacksand`  
**path:** `/Volumes/blacksand/McAfee EERM/encrypted.dsk.98`  
**size_gb:** `2.15`  
**ext:** `.98`  

> File > 1GB warrants manual inspection.

### LARGE_FILE
**Disk:** `blacksand`  
**path:** `/Volumes/blacksand/McAfee EERM/encrypted.dsk.97`  
**size_gb:** `2.15`  
**ext:** `.97`  

> File > 1GB warrants manual inspection.

### LARGE_FILE
**Disk:** `blacksand`  
**path:** `/Volumes/blacksand/McAfee EERM/encrypted.dsk.96`  
**size_gb:** `2.15`  
**ext:** `.96`  

> File > 1GB warrants manual inspection.

### LARGE_FILE
**Disk:** `blacksand`  
**path:** `/Volumes/blacksand/McAfee EERM/encrypted.dsk.95`  
**size_gb:** `2.15`  
**ext:** `.95`  

> File > 1GB warrants manual inspection.

### EXTENSION_ANOMALY
**Disk:** `blacksand`  
**ext:** `.dll`  
**count:** `1`  
**bytes:** `781888`  

> Windows library — investigate purpose

### MULTI_VOLUME_ARCHIVES
**Disk:** `blacksand`  
**count:** `1`  
**groups:** `{'encrypted.dsk': 366}`  

> Large spanned archives — may contain comprehensive data dumps. Central directory read needed to enumerate inner entries.

### LARGE_FILE
**Disk:** `blacksand`  
**path:** `/Volumes/blacksand/McAfee EERM/encrypted.dsk.99`  
**size_gb:** `2.15`  
**ext:** `.99`  

> File > 1GB warrants manual inspection.

### LARGE_FILE
**Disk:** `blacksand`  
**path:** `/Volumes/blacksand/McAfee EERM/encrypted.dsk.98`  
**size_gb:** `2.15`  
**ext:** `.98`  

> File > 1GB warrants manual inspection.

### LARGE_FILE
**Disk:** `blacksand`  
**path:** `/Volumes/blacksand/McAfee EERM/encrypted.dsk.97`  
**size_gb:** `2.15`  
**ext:** `.97`  

> File > 1GB warrants manual inspection.

### LARGE_FILE
**Disk:** `blacksand`  
**path:** `/Volumes/blacksand/McAfee EERM/encrypted.dsk.96`  
**size_gb:** `2.15`  
**ext:** `.96`  

> File > 1GB warrants manual inspection.

### LARGE_FILE
**Disk:** `blacksand`  
**path:** `/Volumes/blacksand/McAfee EERM/encrypted.dsk.95`  
**size_gb:** `2.15`  
**ext:** `.95`  

> File > 1GB warrants manual inspection.

### EXTENSION_ANOMALY
**Disk:** `blacksand`  
**ext:** `.dll`  
**count:** `1`  
**bytes:** `781888`  

> Windows library — investigate purpose

### MULTI_VOLUME_ARCHIVES
**Disk:** `blacksand`  
**count:** `1`  
**groups:** `{'encrypted.dsk': 366}`  

> Large spanned archives — may contain comprehensive data dumps. Central directory read needed to enumerate inner entries.

### LARGE_FILE
**Disk:** `blacksand`  
**path:** `/Volumes/blacksand/McAfee EERM/encrypted.dsk.99`  
**size_gb:** `2.15`  
**ext:** `.99`  

> File > 1GB warrants manual inspection.

### LARGE_FILE
**Disk:** `blacksand`  
**path:** `/Volumes/blacksand/McAfee EERM/encrypted.dsk.98`  
**size_gb:** `2.15`  
**ext:** `.98`  

> File > 1GB warrants manual inspection.

### LARGE_FILE
**Disk:** `blacksand`  
**path:** `/Volumes/blacksand/McAfee EERM/encrypted.dsk.97`  
**size_gb:** `2.15`  
**ext:** `.97`  

> File > 1GB warrants manual inspection.

### LARGE_FILE
**Disk:** `blacksand`  
**path:** `/Volumes/blacksand/McAfee EERM/encrypted.dsk.96`  
**size_gb:** `2.15`  
**ext:** `.96`  

> File > 1GB warrants manual inspection.

### LARGE_FILE
**Disk:** `blacksand`  
**path:** `/Volumes/blacksand/McAfee EERM/encrypted.dsk.95`  
**size_gb:** `2.15`  
**ext:** `.95`  

> File > 1GB warrants manual inspection.

### EXTENSION_ANOMALY
**Disk:** `creamsam`  
**ext:** `.dll`  
**count:** `1`  
**bytes:** `781376`  

> Windows library — investigate purpose

### EXTENSION_ANOMALY
**Disk:** `creamsam`  
**ext:** `.db`  
**count:** `4`  
**bytes:** `385753088`  

> database file — may contain evidence management metadata

### LARGE_FILE
**Disk:** `creamsam`  
**path:** `/Volumes/creamsam/NATIVES/0002/RedmondTax391798.1`  
**size_gb:** `2.15`  
**ext:** `.1`  

> File > 1GB warrants manual inspection.

### LARGE_FILE
**Disk:** `creamsam`  
**path:** `/Volumes/creamsam/NATIVES/0002/RedmondTax391797.dsk`  
**size_gb:** `2.15`  
**ext:** `.dsk`  

> File > 1GB warrants manual inspection.

### LARGE_FILE
**Disk:** `creamsam`  
**path:** `/Volumes/creamsam/NATIVES/0001/RedmondTax023591.mp4`  
**size_gb:** `1.36`  
**ext:** `.mp4`  

> File > 1GB warrants manual inspection.

### LARGE_FILE
**Disk:** `creamsam`  
**path:** `/Volumes/creamsam/.Spotlight-V100/Store-V2/4A98CA24-5CF3-4481-938F-2FDFE1025F12/live.0.indexPositions`  
**size_gb:** `1.2`  
**ext:** `.indexpositions`  

> File > 1GB warrants manual inspection.

### LARGE_FILE
**Disk:** `creamsam`  
**path:** `/Volumes/creamsam/.Spotlight-V100/Store-V2/4A98CA24-5CF3-4481-938F-2FDFE1025F12/live.1.indexPositions`  
**size_gb:** `1.15`  
**ext:** `.indexpositions`  

> File > 1GB warrants manual inspection.

### ACTOR_IN_PATH
**Disk:** `creamsam`  
**actor:** `redmond`  
**example_paths:** `['/Volumes/creamsam/NATIVES/0002/RedmondTax391798.1', '/Volumes/creamsam/NATIVES/0002/RedmondTax391797.dsk', '/Volumes/creamsam/NATIVES/0001/RedmondTax023591.mp4']`  

> Key actor "redmond" appears in file/directory names. Review for relevance to carrier defense or Brady material.

### EXTENSION_ANOMALY
**Disk:** `creamsam`  
**ext:** `.dll`  
**count:** `1`  
**bytes:** `781376`  

> Windows library — investigate purpose

### EXTENSION_ANOMALY
**Disk:** `creamsam`  
**ext:** `.db`  
**count:** `4`  
**bytes:** `385753088`  

> database file — may contain evidence management metadata

### LARGE_FILE
**Disk:** `creamsam`  
**path:** `/Volumes/creamsam/NATIVES/0002/RedmondTax391798.1`  
**size_gb:** `2.15`  
**ext:** `.1`  

> File > 1GB warrants manual inspection.

### LARGE_FILE
**Disk:** `creamsam`  
**path:** `/Volumes/creamsam/NATIVES/0002/RedmondTax391797.dsk`  
**size_gb:** `2.15`  
**ext:** `.dsk`  

> File > 1GB warrants manual inspection.

### LARGE_FILE
**Disk:** `creamsam`  
**path:** `/Volumes/creamsam/NATIVES/0001/RedmondTax023591.mp4`  
**size_gb:** `1.36`  
**ext:** `.mp4`  

> File > 1GB warrants manual inspection.

### LARGE_FILE
**Disk:** `creamsam`  
**path:** `/Volumes/creamsam/.Spotlight-V100/Store-V2/4A98CA24-5CF3-4481-938F-2FDFE1025F12/live.0.indexPositions`  
**size_gb:** `1.2`  
**ext:** `.indexpositions`  

> File > 1GB warrants manual inspection.

### LARGE_FILE
**Disk:** `creamsam`  
**path:** `/Volumes/creamsam/.Spotlight-V100/Store-V2/4A98CA24-5CF3-4481-938F-2FDFE1025F12/live.1.indexPositions`  
**size_gb:** `1.15`  
**ext:** `.indexpositions`  

> File > 1GB warrants manual inspection.

### ACTOR_IN_PATH
**Disk:** `creamsam`  
**actor:** `redmond`  
**example_paths:** `['/Volumes/creamsam/NATIVES/0002/RedmondTax391798.1', '/Volumes/creamsam/NATIVES/0002/RedmondTax391797.dsk', '/Volumes/creamsam/NATIVES/0001/RedmondTax023591.mp4']`  

> Key actor "redmond" appears in file/directory names. Review for relevance to carrier defense or Brady material.

### EXTENSION_ANOMALY
**Disk:** `creamsam`  
**ext:** `.dll`  
**count:** `1`  
**bytes:** `781376`  

> Windows library — investigate purpose

### EXTENSION_ANOMALY
**Disk:** `creamsam`  
**ext:** `.db`  
**count:** `4`  
**bytes:** `386146304`  

> database file — may contain evidence management metadata

### LARGE_FILE
**Disk:** `creamsam`  
**path:** `/Volumes/creamsam/NATIVES/0002/RedmondTax391798.1`  
**size_gb:** `2.15`  
**ext:** `.1`  

> File > 1GB warrants manual inspection.

### LARGE_FILE
**Disk:** `creamsam`  
**path:** `/Volumes/creamsam/NATIVES/0002/RedmondTax391797.dsk`  
**size_gb:** `2.15`  
**ext:** `.dsk`  

> File > 1GB warrants manual inspection.

### LARGE_FILE
**Disk:** `creamsam`  
**path:** `/Volumes/creamsam/NATIVES/0001/RedmondTax023591.mp4`  
**size_gb:** `1.36`  
**ext:** `.mp4`  

> File > 1GB warrants manual inspection.

### LARGE_FILE
**Disk:** `creamsam`  
**path:** `/Volumes/creamsam/.Spotlight-V100/Store-V2/4A98CA24-5CF3-4481-938F-2FDFE1025F12/live.0.indexPositions`  
**size_gb:** `1.2`  
**ext:** `.indexpositions`  

> File > 1GB warrants manual inspection.

### LARGE_FILE
**Disk:** `creamsam`  
**path:** `/Volumes/creamsam/.Spotlight-V100/Store-V2/4A98CA24-5CF3-4481-938F-2FDFE1025F12/live.1.indexPositions`  
**size_gb:** `1.15`  
**ext:** `.indexpositions`  

> File > 1GB warrants manual inspection.

### ACTOR_IN_PATH
**Disk:** `creamsam`  
**actor:** `redmond`  
**example_paths:** `['/Volumes/creamsam/NATIVES/0002/RedmondTax391798.1', '/Volumes/creamsam/NATIVES/0002/RedmondTax391797.dsk', '/Volumes/creamsam/NATIVES/0001/RedmondTax023591.mp4']`  

> Key actor "redmond" appears in file/directory names. Review for relevance to carrier defense or Brady material.

### EXTENSION_ANOMALY
**Disk:** `usbmemorex`  
**ext:** `.db`  
**count:** `3`  
**bytes:** `21598208`  

> database file — may contain evidence management metadata

### ACTOR_IN_PATH
**Disk:** `usbmemorex`  
**actor:** `redmond`  
**example_paths:** `['/Volumes/usbmemorex/TEXT/0016/RedmondTax431631.txt', '/Volumes/usbmemorex/TEXT/0011/RedmondTax334298.txt', '/Volumes/usbmemorex/TEXT/0010/RedmondTax298629.txt']`  

> Key actor "redmond" appears in file/directory names. Review for relevance to carrier defense or Brady material.

### EXTENSION_ANOMALY
**Disk:** `usbmemorex`  
**ext:** `.db`  
**count:** `3`  
**bytes:** `21598208`  

> database file — may contain evidence management metadata

### ACTOR_IN_PATH
**Disk:** `usbmemorex`  
**actor:** `redmond`  
**example_paths:** `['/Volumes/usbmemorex/TEXT/0016/RedmondTax431631.txt', '/Volumes/usbmemorex/TEXT/0011/RedmondTax334298.txt', '/Volumes/usbmemorex/TEXT/0010/RedmondTax298629.txt']`  

> Key actor "redmond" appears in file/directory names. Review for relevance to carrier defense or Brady material.

### EXTENSION_ANOMALY
**Disk:** `usbmemorex`  
**ext:** `.db`  
**count:** `3`  
**bytes:** `21598208`  

> database file — may contain evidence management metadata

### ACTOR_IN_PATH
**Disk:** `usbmemorex`  
**actor:** `redmond`  
**example_paths:** `['/Volumes/usbmemorex/TEXT/0016/RedmondTax431631.txt', '/Volumes/usbmemorex/TEXT/0011/RedmondTax334298.txt', '/Volumes/usbmemorex/TEXT/0010/RedmondTax298629.txt']`  

> Key actor "redmond" appears in file/directory names. Review for relevance to carrier defense or Brady material.

## INFO (11)

### UNSTRUCTURED_DUMP
**Disk:** `T7`  
**top_dirs:** `['$RECYCLE.BIN', '.', 'System Volume Information']`  

> No standard production directory naming. Could be raw device dump rather than curated production. Check for forensic image files (.e01, .vmdk).

### UNSTRUCTURED_DUMP
**Disk:** `T7`  
**top_dirs:** `['$RECYCLE.BIN', '.', 'System Volume Information']`  

> No standard production directory naming. Could be raw device dump rather than curated production. Check for forensic image files (.e01, .vmdk).

### UNSTRUCTURED_DUMP
**Disk:** `blacksand`  
**top_dirs:** `['.', 'McAfee EERM', 'McAfee Removable Media Protection.app']`  

> No standard production directory naming. Could be raw device dump rather than curated production. Check for forensic image files (.e01, .vmdk).

### UNSTRUCTURED_DUMP
**Disk:** `blacksand`  
**top_dirs:** `['.', 'McAfee EERM', 'McAfee Removable Media Protection.app']`  

> No standard production directory naming. Could be raw device dump rather than curated production. Check for forensic image files (.e01, .vmdk).

### UNSTRUCTURED_DUMP
**Disk:** `blacksand`  
**top_dirs:** `['.', 'McAfee EERM', 'McAfee Removable Media Protection.app']`  

> No standard production directory naming. Could be raw device dump rather than curated production. Check for forensic image files (.e01, .vmdk).

### UNSTRUCTURED_DUMP
**Disk:** `creamsam`  
**top_dirs:** `['.', '.Spotlight-V100', '.Trashes', '.fseventsd', '30(b)(6)', 'Alan Redmond', 'Arthur Walsh', 'DATA', 'DOL civil wage litigation with Bene Market-selected', 'Discovery Production US v. Redmond, 24-cr-376-selected']`  

> No standard production directory naming. Could be raw device dump rather than curated production. Check for forensic image files (.e01, .vmdk).

### UNSTRUCTURED_DUMP
**Disk:** `creamsam`  
**top_dirs:** `['.', '.Spotlight-V100', '.Trashes', '.fseventsd', '30(b)(6)', 'Alan Redmond', 'Arthur Walsh', 'DATA', 'DOL civil wage litigation with Bene Market-selected', 'Discovery Production US v. Redmond, 24-cr-376-selected']`  

> No standard production directory naming. Could be raw device dump rather than curated production. Check for forensic image files (.e01, .vmdk).

### UNSTRUCTURED_DUMP
**Disk:** `creamsam`  
**top_dirs:** `['.', '.Spotlight-V100', '.Trashes', '.fseventsd', '30(b)(6)', 'Alan Redmond', 'Arthur Walsh', 'DATA', 'DOL civil wage litigation with Bene Market-selected', 'Discovery Production US v. Redmond, 24-cr-376-selected']`  

> No standard production directory naming. Could be raw device dump rather than curated production. Check for forensic image files (.e01, .vmdk).

### UNSTRUCTURED_DUMP
**Disk:** `usbmemorex`  
**top_dirs:** `['.Spotlight-V100', 'System Volume Information', 'TEXT']`  

> No standard production directory naming. Could be raw device dump rather than curated production. Check for forensic image files (.e01, .vmdk).

### UNSTRUCTURED_DUMP
**Disk:** `usbmemorex`  
**top_dirs:** `['.Spotlight-V100', 'System Volume Information', 'TEXT']`  

> No standard production directory naming. Could be raw device dump rather than curated production. Check for forensic image files (.e01, .vmdk).

### UNSTRUCTURED_DUMP
**Disk:** `usbmemorex`  
**top_dirs:** `['.Spotlight-V100', '.fseventsd', 'System Volume Information', 'TEXT']`  

> No standard production directory naming. Could be raw device dump rather than curated production. Check for forensic image files (.e01, .vmdk).
