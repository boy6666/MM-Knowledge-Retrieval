package com.repair.repository;

import com.repair.entity.Guidance;
import org.springframework.data.domain.Page;
import org.springframework.data.domain.Pageable;
import org.springframework.data.jpa.repository.JpaRepository;

public interface GuidanceRepository extends JpaRepository<Guidance, Integer> {
    Page<Guidance> findByAuthorId(Integer authorId, Pageable pageable);
    Page<Guidance> findByIsPublicTrue(Pageable pageable);
    Page<Guidance> findByIsPublicTrueAndDeviceType(boolean isPublic, String deviceType, Pageable pageable);
    Page<Guidance> findByIsPublicTrueAndFaultType(boolean isPublic, String faultType, Pageable pageable);
}
