package com.agri.agriData.entity;

import jakarta.persistence.Column;
import jakarta.persistence.Entity;
import jakarta.persistence.GeneratedValue;
import jakarta.persistence.GenerationType;
import jakarta.persistence.Id;
import jakarta.persistence.PrePersist;
import jakarta.persistence.PreUpdate;
import jakarta.persistence.Table;

import java.time.OffsetDateTime;

@Entity
@Table(name = "yield_records")
public class YieldRecord {

    @Id
    @GeneratedValue(strategy = GenerationType.IDENTITY)
    private Long id;

    @Column(nullable = false)
    private String country;

    @Column(nullable = false)
    private String crop;

    @Column(nullable = false)
    private Integer year;

    @Column(nullable = false)
    private Double rainMmPerYear;

    @Column(nullable = false)
    private Double pesticidesTonnes;

    @Column(nullable = false)
    private Double avgTemp;

    @Column(nullable = false)
    private Double yieldValue;

    @Column(nullable = false, length = 80)
    private String datasetVersion = "manual-v1";

    @Column(nullable = false, length = 120)
    private String sourceName = "api";

    @Column(nullable = false, length = 64)
    private String datasetHash = "";

    @Column(nullable = false, length = 64)
    private String importBatchId = "";

    @Column(nullable = false)
    private OffsetDateTime ingestedAt;

    @Column(nullable = false)
    private OffsetDateTime updatedAt;

    @PrePersist
    public void prePersist() {
        OffsetDateTime now = OffsetDateTime.now();
        if (ingestedAt == null) {
            ingestedAt = now;
        }
        updatedAt = now;
    }

    @PreUpdate
    public void preUpdate() {
        updatedAt = OffsetDateTime.now();
    }

    public Long getId() {
        return id;
    }

    public void setId(Long id) {
        this.id = id;
    }

    public String getCountry() {
        return country;
    }

    public void setCountry(String country) {
        this.country = country;
    }

    public String getCrop() {
        return crop;
    }

    public void setCrop(String crop) {
        this.crop = crop;
    }

    public Integer getYear() {
        return year;
    }

    public void setYear(Integer year) {
        this.year = year;
    }

    public Double getRainMmPerYear() {
        return rainMmPerYear;
    }

    public void setRainMmPerYear(Double rainMmPerYear) {
        this.rainMmPerYear = rainMmPerYear;
    }

    public Double getPesticidesTonnes() {
        return pesticidesTonnes;
    }

    public void setPesticidesTonnes(Double pesticidesTonnes) {
        this.pesticidesTonnes = pesticidesTonnes;
    }

    public Double getAvgTemp() {
        return avgTemp;
    }

    public void setAvgTemp(Double avgTemp) {
        this.avgTemp = avgTemp;
    }

    public Double getYieldValue() {
        return yieldValue;
    }

    public void setYieldValue(Double yieldValue) {
        this.yieldValue = yieldValue;
    }

    public String getDatasetVersion() {
        return datasetVersion;
    }

    public void setDatasetVersion(String datasetVersion) {
        this.datasetVersion = datasetVersion;
    }

    public String getSourceName() {
        return sourceName;
    }

    public void setSourceName(String sourceName) {
        this.sourceName = sourceName;
    }

    public String getDatasetHash() {
        return datasetHash;
    }

    public void setDatasetHash(String datasetHash) {
        this.datasetHash = datasetHash;
    }

    public String getImportBatchId() {
        return importBatchId;
    }

    public void setImportBatchId(String importBatchId) {
        this.importBatchId = importBatchId;
    }

    public OffsetDateTime getIngestedAt() {
        return ingestedAt;
    }

    public void setIngestedAt(OffsetDateTime ingestedAt) {
        this.ingestedAt = ingestedAt;
    }

    public OffsetDateTime getUpdatedAt() {
        return updatedAt;
    }

    public void setUpdatedAt(OffsetDateTime updatedAt) {
        this.updatedAt = updatedAt;
    }
}
