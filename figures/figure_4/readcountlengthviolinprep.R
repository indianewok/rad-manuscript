library(dplyr)
library(readr)

#write csv for counts per barcode plot 

df1 <- read.csv("read.lengths.1.6.26/splitseq_extracted_headers.csv")
barcode_counts_df1 <- df1 %>%
  count(final_barcode, name = "count")
write_csv(barcode_counts_df1, "read.lengths.1.6.26/split_seq_final_barcode_counts.csv")

df2 <- read.csv("read.lengths.1.6.26/scmix2_extracted_headers.csv")
barcode_counts_df2 <- df2 %>%
  count(final_barcode, name = "count")
write_csv(barcode_counts_df2, "read.lengths.1.6.26/scmix2_final_barcode_counts.csv")

df3 <- read.csv("read.lengths.1.6.26/nbc_extracted_headers.csv")
barcode_counts_df3 <- df3 %>%
  count(final_barcode, name = "count")
write_csv(barcode_counts_df3, "read.lengths.1.6.26/nbc_final_barcode_counts.csv")

df4 <- read.csv("read.lengths.1.6.26/rsq_extracted_headers.csv")
barcode_counts_df4 <- df4 %>%
  count(final_barcode, name = "count")
write_csv(barcode_counts_df4, "read.lengths.1.6.26/rsq_final_barcode_counts.csv")

#downselect data to 100,000 read lengths for each dataset and write csv

set.seed(123)  # for reproducibility
df_sampled1 <- df1 %>%
  slice_sample(n = 100000)
# Write to single-column CSV
write_csv(df_sampled1, "read.lengths.1.6.26/splitseq_sampled_readlengths.csv")

set.seed(123)  # for reproducibility
df_sampled2 <- df2 %>%
  slice_sample(n = 100000)
# Write to single-column CSV
write_csv(df_sampled2, "read.lengths.1.6.26/scmix2_sampled_readlengths.csv")

set.seed(123)  # for reproducibility
df_sampled3 <- df3 %>%
  slice_sample(n = 100000)
# Write to single-column CSV
write_csv(df_sampled3, "read.lengths.1.6.26/nbc_sampled_readlengths.csv")

set.seed(123)  # for reproducibility
df_sampled4 <- df4 %>%
  slice_sample(n = 100000)
# Write to single-column CSV
write_csv(df_sampled4, "read.lengths.1.6.26/rsq_sampled_readlengths.csv")




