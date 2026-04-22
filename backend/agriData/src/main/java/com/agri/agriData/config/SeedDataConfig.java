package com.agri.agriData.config;

import com.agri.agriData.entity.YieldRecord;
import com.agri.agriData.repository.YieldRecordRepository;
import org.springframework.boot.CommandLineRunner;
import org.springframework.context.annotation.Bean;
import org.springframework.context.annotation.Configuration;

@Configuration
public class SeedDataConfig {

    @Bean
    CommandLineRunner seedYieldRecords(YieldRecordRepository repository) {
        return args -> {
            if (repository.count() > 0) {
                return;
            }

            YieldRecord r1 = new YieldRecord();
            r1.setCountry("Cameroon");
            r1.setCrop("Maize");
            r1.setYear(2023);
            r1.setRainMmPerYear(1650.0);
            r1.setPesticidesTonnes(140.0);
            r1.setAvgTemp(24.5);
            r1.setYieldValue(38200.0);

            YieldRecord r2 = new YieldRecord();
            r2.setCountry("Cameroon");
            r2.setCrop("Rice");
            r2.setYear(2023);
            r2.setRainMmPerYear(1800.0);
            r2.setPesticidesTonnes(210.0);
            r2.setAvgTemp(25.0);
            r2.setYieldValue(45100.0);

            repository.save(r1);
            repository.save(r2);
        };
    }
}
