suppressMessages(library(data.table))
b1 <- fread("/tmp/b1_whitelist.csv", header=FALSE)$V1
b2 <- fread("/tmp/b2_whitelist.csv", header=FALSE)$V1
full_wl <- fread("/Users/cmv/Desktop/rad_paper/barcode_whitelists/rageseq_full_bcs.csv")$barcode
b1_tp <- sum(b1 %in% full_wl); b1_fp <- length(b1) - b1_tp
b2_tp <- sum(b2 %in% full_wl); b2_fp <- length(b2) - b2_tp
cat(sprintf("BLAZE B1 (default): n=%d  TP=%d  FP=%d\n", length(b1), b1_tp, b1_fp))
cat(sprintf("BLAZE B2 (HS):      n=%d  TP=%d  FP=%d\n", length(b2), b2_tp, b2_fp))
cat(sprintf("\n  Delta TP  (HS - default): %+d   [manuscript: +433]\n", b2_tp - b1_tp))
cat(sprintf("  Delta FP  (HS - default): %+d   [reading A]\n", b2_fp - b1_fp))
cat(sprintf("  Total FP  (HS absolute):  %d    [reading B]\n", b2_fp))
cat("\nManuscript says: 'HS generated an additional 1,259 total false positive barcodes, compared to the 91 false positives from BLAZE's default mode'\n")
cat(sprintf("  Reading A (delta): HS adds +%d FPs, claim +1,259 — %s\n", b2_fp-b1_fp, if (b2_fp-b1_fp == 1259) "MATCH" else "MISMATCH"))
cat(sprintf("  Reading B (absolute): HS total FPs = %d, claim 1,259 — %s\n", b2_fp, if (b2_fp == 1259) "MATCH" else "MISMATCH"))
