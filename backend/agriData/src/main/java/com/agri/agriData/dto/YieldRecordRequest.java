package com.agri.agriData.dto;

import jakarta.validation.constraints.Max;
import jakarta.validation.constraints.Min;
import jakarta.validation.constraints.NotBlank;
import jakarta.validation.constraints.NotNull;
import jakarta.validation.constraints.Size;
import org.hibernate.validator.constraints.Range;

public record YieldRecordRequest(
        @NotBlank String country,
        @NotBlank String crop,
        @NotNull @Min(1960) @Max(2100) Integer year,
        @NotNull @Range(min = 0, max = 10000) Double rainMmPerYear,
        @NotNull @Range(min = 0, max = 1000000) Double pesticidesTonnes,
        @NotNull @Range(min = -50, max = 80) Double avgTemp,
        @NotNull @Range(min = 0, max = 2000000) Double yieldValue,
        @Size(max = 80) String datasetVersion,
        @Size(max = 120) String sourceName,
        @Size(max = 64) String importBatchId
) {
}
