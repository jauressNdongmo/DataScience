package com.agri.agriData.service;

import com.agri.agriData.dto.BulkValidationResponse;
import com.agri.agriData.dto.DatasetSummaryResponse;
import com.agri.agriData.dto.RecordCoverageResponse;
import com.agri.agriData.dto.ValidationIssue;
import com.agri.agriData.dto.YieldRecordRequest;
import com.agri.agriData.entity.YieldRecord;
import com.agri.agriData.repository.DatasetSummaryProjection;
import com.agri.agriData.repository.YieldRecordRepository;
import org.springframework.stereotype.Service;

import java.nio.charset.StandardCharsets;
import java.security.MessageDigest;
import java.security.NoSuchAlgorithmException;
import java.util.ArrayList;
import java.util.HexFormat;
import java.util.List;
import java.util.Locale;
import java.util.UUID;

@Service
public class YieldRecordService {

    private final YieldRecordRepository repository;

    public YieldRecordService(YieldRecordRepository repository) {
        this.repository = repository;
    }

    public List<YieldRecord> findAll() {
        return repository.findAll();
    }

    public List<YieldRecord> findByCountryAndCrop(String country, String crop) {
        return repository.findByCountryIgnoreCaseAndCropIgnoreCase(country, crop);
    }

    public BulkValidationResponse validateBulk(List<YieldRecordRequest> requests) {
        List<ValidationIssue> issues = new ArrayList<>();
        for (int i = 0; i < requests.size(); i++) {
            YieldRecordRequest req = requests.get(i);
            validateRequest(i, req, issues);
        }
        int invalidRows = (int) issues.stream().map(ValidationIssue::rowIndex).distinct().count();
        int totalRows = requests.size();
        int validRows = Math.max(0, totalRows - invalidRows);

        return new BulkValidationResponse(
                totalRows,
                validRows,
                invalidRows,
                issues.isEmpty(),
                issues
        );
    }

    public List<YieldRecord> saveBulk(List<YieldRecordRequest> requests) {
        BulkValidationResponse validation = validateBulk(requests);
        if (!validation.valid()) {
            String reason = validation.issues().stream()
                    .limit(5)
                    .map(issue -> "[row=%d field=%s] %s".formatted(issue.rowIndex(), issue.field(), issue.message()))
                    .reduce((left, right) -> left + "; " + right)
                    .orElse("payload invalide");
            throw new IllegalArgumentException("Bulk import rejeté: " + reason);
        }

        String defaultBatchId = "batch-" + UUID.randomUUID();
        List<YieldRecord> records = requests.stream()
                .map(request -> toEntity(request, defaultBatchId))
                .toList();
        return repository.saveAll(records);
    }

    public YieldRecord update(Long id, YieldRecordRequest request) {
        List<ValidationIssue> issues = new ArrayList<>();
        validateRequest(0, request, issues);
        if (!issues.isEmpty()) {
            throw new IllegalArgumentException(issues.get(0).message());
        }

        YieldRecord existing = repository.findById(id)
                .orElseThrow(() -> new IllegalArgumentException("Record introuvable: " + id));

        applyBusinessFields(existing, request);
        existing.setDatasetVersion(defaultString(request.datasetVersion(), existing.getDatasetVersion(), "manual-v1"));
        existing.setSourceName(defaultString(request.sourceName(), existing.getSourceName(), "api"));
        existing.setImportBatchId(defaultString(request.importBatchId(), existing.getImportBatchId(), "batch-manual"));
        existing.setDatasetHash(hashRecord(existing));
        return repository.save(existing);
    }

    public void delete(Long id) {
        YieldRecord existing = repository.findById(id)
                .orElseThrow(() -> new IllegalArgumentException("Record introuvable: " + id));
        repository.delete(existing);
    }

    public RecordCoverageResponse coverage(String country, String crop) {
        Object[] row = repository.coverage(normalizeNullable(country), normalizeNullable(crop));
        Integer yearMin = row != null && row[0] != null ? ((Number) row[0]).intValue() : null;
        Integer yearMax = row != null && row[1] != null ? ((Number) row[1]).intValue() : null;
        long rows = row != null && row[2] != null ? ((Number) row[2]).longValue() : 0L;
        return new RecordCoverageResponse(
                normalizeNullable(country),
                normalizeNullable(crop),
                yearMin,
                yearMax,
                rows
        );
    }

    public List<DatasetSummaryResponse> datasetSummaries() {
        List<DatasetSummaryProjection> projections = repository.datasetSummaries();
        return projections.stream()
                .map(item -> new DatasetSummaryResponse(
                        item.getDatasetVersion(),
                        item.getSourceName(),
                        item.getImportBatchId(),
                        item.getRows(),
                        item.getYearMin(),
                        item.getYearMax(),
                        item.getLastIngestedAt()
                ))
                .toList();
    }

    private YieldRecord toEntity(YieldRecordRequest request, String defaultBatchId) {
        YieldRecord record = new YieldRecord();
        applyBusinessFields(record, request);
        record.setDatasetVersion(defaultString(request.datasetVersion(), null, "manual-v1"));
        record.setSourceName(defaultString(request.sourceName(), null, "api"));
        record.setImportBatchId(defaultString(request.importBatchId(), null, defaultBatchId));
        record.setDatasetHash(hashRecord(record));
        return record;
    }

    private void applyBusinessFields(YieldRecord record, YieldRecordRequest request) {
        record.setCountry(request.country().trim());
        record.setCrop(request.crop().trim());
        record.setYear(request.year());
        record.setRainMmPerYear(request.rainMmPerYear());
        record.setPesticidesTonnes(request.pesticidesTonnes());
        record.setAvgTemp(request.avgTemp());
        record.setYieldValue(request.yieldValue());
    }

    private void validateRequest(int rowIndex, YieldRecordRequest request, List<ValidationIssue> issues) {
        if (request.country() == null || request.country().isBlank()) {
            issues.add(new ValidationIssue(rowIndex, "country", "country est obligatoire"));
        }
        if (request.crop() == null || request.crop().isBlank()) {
            issues.add(new ValidationIssue(rowIndex, "crop", "crop est obligatoire"));
        }
        if (request.year() == null || request.year() < 1960 || request.year() > 2100) {
            issues.add(new ValidationIssue(rowIndex, "year", "year doit etre entre 1960 et 2100"));
        }
        if (request.rainMmPerYear() == null || request.rainMmPerYear() < 0 || request.rainMmPerYear() > 10000) {
            issues.add(new ValidationIssue(rowIndex, "rainMmPerYear", "rainMmPerYear hors bornes [0,10000]"));
        }
        if (request.pesticidesTonnes() == null || request.pesticidesTonnes() < 0 || request.pesticidesTonnes() > 1_000_000) {
            issues.add(new ValidationIssue(rowIndex, "pesticidesTonnes", "pesticidesTonnes hors bornes [0,1000000]"));
        }
        if (request.avgTemp() == null || request.avgTemp() < -50 || request.avgTemp() > 80) {
            issues.add(new ValidationIssue(rowIndex, "avgTemp", "avgTemp hors bornes [-50,80]"));
        }
        if (request.yieldValue() == null || request.yieldValue() < 0 || request.yieldValue() > 2_000_000) {
            issues.add(new ValidationIssue(rowIndex, "yieldValue", "yieldValue hors bornes [0,2000000]"));
        }
    }

    private String hashRecord(YieldRecord record) {
        String payload = "%s|%s|%d|%.4f|%.4f|%.4f|%.4f|%s|%s|%s".formatted(
                normalize(record.getCountry()),
                normalize(record.getCrop()),
                record.getYear(),
                record.getRainMmPerYear(),
                record.getPesticidesTonnes(),
                record.getAvgTemp(),
                record.getYieldValue(),
                normalize(record.getDatasetVersion()),
                normalize(record.getSourceName()),
                normalize(record.getImportBatchId())
        );
        try {
            MessageDigest md = MessageDigest.getInstance("SHA-256");
            byte[] digest = md.digest(payload.getBytes(StandardCharsets.UTF_8));
            return HexFormat.of().formatHex(digest);
        } catch (NoSuchAlgorithmException ex) {
            throw new IllegalStateException("SHA-256 indisponible", ex);
        }
    }

    private String normalizeNullable(String value) {
        if (value == null) {
            return null;
        }
        String trimmed = value.trim();
        return trimmed.isEmpty() ? null : trimmed;
    }

    private String normalize(String value) {
        return value == null ? "" : value.trim().toLowerCase(Locale.ROOT);
    }

    private String defaultString(String candidate, String fallback, String defaultValue) {
        if (candidate != null && !candidate.isBlank()) {
            return candidate.trim();
        }
        if (fallback != null && !fallback.isBlank()) {
            return fallback.trim();
        }
        return defaultValue;
    }
}
