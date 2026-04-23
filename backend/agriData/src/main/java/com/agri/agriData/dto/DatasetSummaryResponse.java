package com.agri.agriData.dto;

import java.time.OffsetDateTime;

public record DatasetSummaryResponse(
        String datasetVersion,
        String sourceName,
        String importBatchId,
        long rows,
        Integer yearMin,
        Integer yearMax,
        OffsetDateTime lastIngestedAt
) {
}
