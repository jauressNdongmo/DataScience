package com.agri.agriData.dto;

public record RecordCoverageResponse(
        String country,
        String crop,
        Integer yearMin,
        Integer yearMax,
        long rows
) {
}
