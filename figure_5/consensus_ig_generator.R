msa_consensus <- function(seqs, ambiguity = "N") {
  seqs <- seqs[!is.na(seqs)]
  if (!length(seqs)) {
    return(NA_character_)
  }
  dna <- Biostrings::DNAStringSet(seqs)
  aln <- AlignSeqs(dna)                 # multiple sequence alignment
  cm  <- consensusMatrix(aln)           # A/C/G/T/N/- counts per column
  cons <- consensusString(cm, ambiguity = ambiguity)
  as.character(cons)
}
