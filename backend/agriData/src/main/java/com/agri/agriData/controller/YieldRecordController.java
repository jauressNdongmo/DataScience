package com.agri.agriData.controller;

import com.agri.agriData.dto.YieldRecordRequest;
import com.agri.agriData.entity.YieldRecord;
import com.agri.agriData.service.YieldRecordService;
import jakarta.validation.Valid;
import org.springframework.http.HttpStatus;
import org.springframework.web.bind.annotation.GetMapping;
import org.springframework.web.bind.annotation.PostMapping;
import org.springframework.web.bind.annotation.RequestBody;
import org.springframework.web.bind.annotation.RequestMapping;
import org.springframework.web.bind.annotation.RequestParam;
import org.springframework.web.bind.annotation.ResponseStatus;
import org.springframework.web.bind.annotation.RestController;

import java.util.List;

@RestController
@RequestMapping("/records")
public class YieldRecordController {

    private final YieldRecordService yieldRecordService;

    public YieldRecordController(YieldRecordService yieldRecordService) {
        this.yieldRecordService = yieldRecordService;
    }

    @GetMapping
    public List<YieldRecord> list() {
        return yieldRecordService.findAll();
    }

    @GetMapping("/search")
    public List<YieldRecord> byCountryAndCrop(
            @RequestParam String country,
            @RequestParam String crop
    ) {
        return yieldRecordService.findByCountryAndCrop(country, crop);
    }

    @PostMapping("/bulk")
    @ResponseStatus(HttpStatus.CREATED)
    public List<YieldRecord> createBulk(@RequestBody @Valid List<YieldRecordRequest> records) {
        return yieldRecordService.saveBulk(records);
    }
}
