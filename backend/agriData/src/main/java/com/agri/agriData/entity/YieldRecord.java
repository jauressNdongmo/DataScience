package com.agri.agriData.entity;

import jakarta.persistence.Column;
import jakarta.persistence.Entity;
import jakarta.persistence.GeneratedValue;
import jakarta.persistence.GenerationType;
import jakarta.persistence.Id;
import jakarta.persistence.Table;

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
}
