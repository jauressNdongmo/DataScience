package com.agri.agriData.repository;

import com.agri.agriData.entity.YieldRecord;
import org.springframework.data.jpa.repository.JpaRepository;

import java.util.List;

public interface YieldRecordRepository extends JpaRepository<YieldRecord, Long> {
    List<YieldRecord> findByCountryIgnoreCaseAndCropIgnoreCase(String country, String crop);
}
