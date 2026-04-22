package com.agri.agriData.service;

import com.agri.agriData.dto.YieldRecordRequest;
import com.agri.agriData.entity.YieldRecord;
import com.agri.agriData.repository.YieldRecordRepository;
import org.springframework.stereotype.Service;

import java.util.List;

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

    public List<YieldRecord> saveBulk(List<YieldRecordRequest> requests) {
        List<YieldRecord> records = requests.stream().map(this::toEntity).toList();
        return repository.saveAll(records);
    }

    private YieldRecord toEntity(YieldRecordRequest request) {
        YieldRecord record = new YieldRecord();
        record.setCountry(request.country());
        record.setCrop(request.crop());
        record.setYear(request.year());
        record.setRainMmPerYear(request.rainMmPerYear());
        record.setPesticidesTonnes(request.pesticidesTonnes());
        record.setAvgTemp(request.avgTemp());
        record.setYieldValue(request.yieldValue());
        return record;
    }
}
