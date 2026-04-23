package com.agri.agriData.repository;

import com.agri.agriData.entity.YieldRecord;
import org.springframework.data.jpa.repository.JpaRepository;
import org.springframework.data.repository.query.Param;
import org.springframework.data.jpa.repository.Query;

import java.util.List;
import java.util.Optional;

public interface YieldRecordRepository extends JpaRepository<YieldRecord, Long> {
    List<YieldRecord> findByCountryIgnoreCaseAndCropIgnoreCase(String country, String crop);

    @Query("""
            select
                min(r.year),
                max(r.year),
                count(r.id)
            from YieldRecord r
            where (:country is null or lower(r.country) = lower(:country))
              and (:crop is null or lower(r.crop) = lower(:crop))
            """)
    Object[] coverage(@Param("country") String country, @Param("crop") String crop);

    @Query("""
            select
                r.datasetVersion as datasetVersion,
                r.sourceName as sourceName,
                r.importBatchId as importBatchId,
                count(r.id) as rows,
                min(r.year) as yearMin,
                max(r.year) as yearMax,
                max(r.ingestedAt) as lastIngestedAt
            from YieldRecord r
            group by r.datasetVersion, r.sourceName, r.importBatchId
            order by max(r.ingestedAt) desc
            """)
    List<DatasetSummaryProjection> datasetSummaries();

    Optional<YieldRecord> findById(Long id);
}
