package com.agri.agriData.repository;

import java.time.OffsetDateTime;

public interface DatasetSummaryProjection {
    String getDatasetVersion();
    String getSourceName();
    String getImportBatchId();
    long getRows();
    Integer getYearMin();
    Integer getYearMax();
    OffsetDateTime getLastIngestedAt();
}
