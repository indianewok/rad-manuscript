suppressMessages({library(data.table)})
# Run this script from its own directory (figure_2/), or `cd figure_2/ && Rscript verify_fig2.R`.
load("figure_2_workspace.RData")
rad <- rad_sctagger_headers; blaze <- blaze_sctagger_headers

ok <- function(cond) if (cond) "OK" else "MISMATCH"

cat("====== FIGURE 2 RESULTS TEXT — VERIFICATION ======\n\n")

cat("--- PARA 1: Input data ---\n")
cat(sprintf("Claim: \"5 million error-modified reads\" -> RAD headers: %d  BLAZE headers: %d\n\n", nrow(rad), nrow(blaze)))

cat("--- PARA 2: Barcode discovery (Panels B-D) ---\n")
rad_tp <- sum(rad_counts$final_barcode %in% sctagger_bcs)
rad_fp <- sum(!rad_counts$final_barcode %in% sctagger_bcs)
blaze_tp <- sum(blaze_counts$final_barcode %in% sctagger_bcs)
blaze_fp <- sum(!blaze_counts$final_barcode %in% sctagger_bcs)
cat(sprintf("Claim: RAD 4,997 TP / 33 FP -> ACTUAL %d / %d  %s\n", rad_tp, rad_fp, ok(rad_tp==4997 && rad_fp==33)))
cat(sprintf("Claim: BLAZE 5,000 TP / 607 FP -> ACTUAL %d / %d  %s\n", blaze_tp, blaze_fp, ok(blaze_tp==5000 && blaze_fp==607)))

extra <- blaze_tp - rad_tp
cat(sprintf("Claim: \"0.7%% (n=3) additional true barcodes\"\n"))
cat(sprintf("  n = %d (claim 3): %s\n", extra, ok(extra==3)))
cat(sprintf("  %%: %d/%d = %.3f%% , %d/%d = %.3f%%  ---  claim 0.7%% looks WRONG (actual ~0.06%%)\n",
            extra, rad_tp, 100*extra/rad_tp, extra, blaze_tp, 100*extra/blaze_tp))

cat(sprintf("\nClaim: factor 18.4x (n=574)\n"))
cat(sprintf("  ratio 607/33 = %.3f  %s\n", 607/33, ok(abs(607/33-18.4)<0.1)))
cat(sprintf("  diff 607-33 = %d  %s\n", 607-33, ok(607-33==574)))

cat("\nClaim: F1 RAD 0.996 vs BLAZE 0.943\n")
rad_p <- rad_tp/(rad_tp+rad_fp); rad_s <- rad_tp/5000; rad_f1 <- 2*rad_p*rad_s/(rad_p+rad_s)
blaze_p <- blaze_tp/(blaze_tp+blaze_fp); blaze_s <- blaze_tp/5000; blaze_f1 <- 2*blaze_p*blaze_s/(blaze_p+blaze_s)
cat(sprintf("  RAD F1=%.4f  %s\n", rad_f1, ok(abs(rad_f1-0.996)<0.005)))
cat(sprintf("  BLAZE F1=%.4f  %s\n", blaze_f1, ok(abs(blaze_f1-0.943)<0.005)))

cat("\n--- PARA 3: Demultiplexing (Panels E-H) ---\n")
rad_native_tp <- nrow(rad[corrected==FALSE & incorrect==FALSE])
blaze_native_tp <- nrow(blaze[corrected==FALSE & incorrect==FALSE])
cat(sprintf("Claim: RAD native TP 671,910 -> ACTUAL %d  %s\n", rad_native_tp, ok(rad_native_tp==671910)))
cat(sprintf("Claim: BLAZE native TP 640,957 -> ACTUAL %d  %s\n", blaze_native_tp, ok(blaze_native_tp==640957)))

diff_native <- rad_native_tp - blaze_native_tp
cat(sprintf("Claim: additional 30,953 reads (4.83%% of BLAZE)\n"))
cat(sprintf("  diff %d  %s ;  %.2f%%  %s\n", diff_native, ok(diff_native==30953),
            100*diff_native/blaze_native_tp, ok(abs(100*diff_native/blaze_native_tp-4.83)<0.05)))

cat("\nClaim: mean reads per native TP barcode — RAD 134, BLAZE 128\n")
cat(sprintf("  RAD %d/%d = %.2f  %s\n", rad_native_tp, rad_tp, rad_native_tp/rad_tp, ok(round(rad_native_tp/rad_tp)==134)))
cat(sprintf("  BLAZE %d/%d = %.2f  %s\n", blaze_native_tp, blaze_tp, blaze_native_tp/blaze_tp, ok(round(blaze_native_tp/blaze_tp)==128)))

rad_fp_bcs   <- rad_counts$final_barcode[!rad_counts$final_barcode %in% sctagger_bcs]
blaze_fp_bcs <- blaze_counts$final_barcode[!blaze_counts$final_barcode %in% sctagger_bcs]
rad_fp_reads   <- nrow(rad[final_barcode %in% rad_fp_bcs])
blaze_fp_reads <- nrow(blaze[final_barcode %in% blaze_fp_bcs])
cat(sprintf("\nClaim: BLAZE 37,262 reads to 607 FP, RAD 1,271 reads to 33 FP\n"))
cat(sprintf("  RAD %d  %s\n",   rad_fp_reads,   ok(rad_fp_reads==1271)))
cat(sprintf("  BLAZE %d  %s\n", blaze_fp_reads, ok(blaze_fp_reads==37262)))

rad_fp_native  <- nrow(rad[corrected==FALSE & final_barcode %in% rad_fp_bcs])
rad_fp_corr    <- nrow(rad[corrected==TRUE  & final_barcode %in% rad_fp_bcs])
blaze_fp_native<- nrow(blaze[corrected==FALSE & final_barcode %in% blaze_fp_bcs])
blaze_fp_corr  <- nrow(blaze[corrected==TRUE  & final_barcode %in% blaze_fp_bcs])
cat(sprintf("\nClaim: improper extractions — BLAZE 6,945 / RAD 311\n"))
cat(sprintf("  RAD native->FP-bc:   %d  %s\n", rad_fp_native,   ok(rad_fp_native==311)))
cat(sprintf("  BLAZE native->FP-bc: %d  %s\n", blaze_fp_native, ok(blaze_fp_native==6945)))
cat(sprintf("Claim: invalid error corrections — BLAZE 30,317 / RAD 960\n"))
cat(sprintf("  RAD corr->FP-bc:   %d  %s\n", rad_fp_corr,   ok(rad_fp_corr==960)))
cat(sprintf("  BLAZE corr->FP-bc: %d  %s\n", blaze_fp_corr, ok(blaze_fp_corr==30317)))

cat(sprintf("\nClaim: \"1.5x more mean reads BLAZE n=61 vs RAD n=38\" per FP bc\n"))
cat(sprintf("  RAD %d/%d = %.2f  %s\n",   rad_fp_reads, rad_fp, rad_fp_reads/rad_fp, ok(round(rad_fp_reads/rad_fp)==38)))
cat(sprintf("  BLAZE %d/%d = %.2f  %s\n", blaze_fp_reads, blaze_fp, blaze_fp_reads/blaze_fp, ok(round(blaze_fp_reads/blaze_fp)==61)))
ratio <- (blaze_fp_reads/blaze_fp)/(rad_fp_reads/rad_fp)
cat(sprintf("  ratio %.2fx  %s\n", ratio, ok(abs(ratio-1.5)<0.2)))

cat("\n--- PARA 4: Error-corrected (Panels I-J) ---\n")
rad_corr_ok  <- nrow(rad[corrected==TRUE & incorrect==FALSE])
rad_corr_bad <- nrow(rad[corrected==TRUE & incorrect==TRUE])
blaze_corr_ok  <- nrow(blaze[corrected==TRUE & incorrect==FALSE])
blaze_corr_bad <- nrow(blaze[corrected==TRUE & incorrect==TRUE])
cat(sprintf("Claim: RAD 1,855,725 correctly corrected vs BLAZE 1,809,839 (diff 45,886)\n"))
cat(sprintf("  RAD %d   %s\n", rad_corr_ok, ok(rad_corr_ok==1855725)))
cat(sprintf("  BLAZE %d %s\n", blaze_corr_ok, ok(blaze_corr_ok==1809839)))
cat(sprintf("  diff %d  %s\n", rad_corr_ok-blaze_corr_ok, ok(rad_corr_ok-blaze_corr_ok==45886)))

cat(sprintf("\nClaim: BLAZE improper 153,682  /  RAD improper 180,519  /  diff 26,837\n"))
cat(sprintf("  RAD %d   %s\n", rad_corr_bad, ok(rad_corr_bad==180519)))
cat(sprintf("  BLAZE %d %s\n", blaze_corr_bad, ok(blaze_corr_bad==153682)))
cat(sprintf("  diff %d  %s\n", rad_corr_bad-blaze_corr_bad, ok(rad_corr_bad-blaze_corr_bad==26837)))
cat("NOTE: text says \"improperly corrected a total of 153,682 BARCODES\" — should be READS\n")

cat("\n--- PARA 5: Edit distance caveat (Supplemental S2) ---\n")
print(sctagger_raw_cts[edit_dist <= 3])
ed1 <- sctagger_raw_cts[edit_dist==1]
cat(sprintf("\nClaim: 8.57x more likely within ED=1 vs randomly sampled reps\n"))
cat(sprintf("  ScTagger ED1 = %d\n", ed1$sctagger))
cat(sprintf("  Mean reps    = %.2f ;  ScTagger/Mean_rep = %.2fx\n", mean(c(ed1$rep1,ed1$rep2,ed1$rep3)), ed1$sctagger/mean(c(ed1$rep1,ed1$rep2,ed1$rep3))))
cat(sprintf("  rep1         = %d ;  ScTagger/rep1     = %.2fx  (claim 8.57)  %s\n", ed1$rep1, ed1$sctagger/ed1$rep1, ok(abs(ed1$sctagger/ed1$rep1-8.57)<0.1)))

cat(sprintf("\nClaim: 5x more likely vs LA1\n"))
cat(sprintf("  ScTagger/LA1 = %d/%d = %.2fx  %s\n", ed1$sctagger, ed1$la1, ed1$sctagger/ed1$la1, ok(ed1$sctagger/ed1$la1==5)))

cat("\n--- PARA 6: Edit distance ED_final<=ED_true (Supplemental S3) ---\n")
shared_incorrect <- intersect(venn_overlap$rad, venn_overlap$BLAZE)
cat(sprintf("Claim: shared set of reads ~97k\n"))
cat(sprintf("  |RAD incorrect ∩ BLAZE incorrect| = %d  %s\n", length(shared_incorrect), ok(abs(length(shared_incorrect)-97000)<5000)))

cat("\n====== END VERIFICATION ======\n")
