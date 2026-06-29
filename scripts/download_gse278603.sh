#!/bin/bash
# Download GSE278603 spatial transcriptomics data (mouse embryo organogenesis)
# Dataset: Digital reconstruction of full embryos during early mouse organogenesis
# Paper: https://doi.org/10.1016/j.cell.2025.05.035

set -e

DATA_DIR="data/GSE278603"
mkdir -p "$DATA_DIR"

FTP_BASE="ftp.ncbi.nlm.nih.gov/geo/series/GSE278nnn/GSE278603/suppl"

echo "========================================"
echo "GSE278603 Download Script"
echo "========================================"
echo ""
echo "Attempting FTP download..."
curl -s --ftp-pasv "ftp://$FTP_BASE/" 2>/dev/null | head -30

BASE_URL="https://ftp.ncbi.nlm.nih.gov/geo/series/GSE278nnn/GSE278603/suppl"

for TRY in "GSE278603_RAW.tar" "GSE278603_processed_data.h5ad.gz" "GSE278603_E9.5.h5ad.gz" "GSE278603_embryo1.h5ad.gz"; do
    echo "Trying: $TRY ..."
    wget --no-check-certificate -nv -P "$DATA_DIR" "$BASE_URL/$TRY" 2>&1 && echo "SUCCESS: $TRY" || echo "Not found: $TRY"
done

echo ""
echo "========================================"
echo "If downloads failed:"
echo "1. Open: https://www.ncbi.nlm.nih.gov/geo/query/acc.cgi?acc=GSE278603"
echo "2. Click 'Supplementary file' at the bottom"
echo "3. Download .h5ad files and place in: $DATA_DIR"
echo "========================================"
