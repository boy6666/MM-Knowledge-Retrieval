package com.repair.repository;

import com.repair.entity.CommunityPost;
import org.springframework.data.domain.Page;
import org.springframework.data.domain.Pageable;
import org.springframework.data.jpa.repository.JpaRepository;
import org.springframework.data.jpa.repository.Query;
import org.springframework.data.repository.query.Param;

public interface CommunityPostRepository extends JpaRepository<CommunityPost, Integer> {
    Page<CommunityPost> findByStatus(String status, Pageable pageable);
    Page<CommunityPost> findByAuthorId(Integer authorId, Pageable pageable);
    Page<CommunityPost> findByStatusAndDeviceType(String status, String deviceType, Pageable pageable);
    Page<CommunityPost> findByStatusAndFaultType(String status, String faultType, Pageable pageable);
    @Query("SELECT p FROM CommunityPost p WHERE p.status = :status AND p.deviceType = :deviceType AND p.faultType = :faultType")
    Page<CommunityPost> findByStatusAndDeviceTypeAndFaultType(
            @Param("status") String status,
            @Param("deviceType") String deviceType,
            @Param("faultType") String faultType,
            Pageable pageable);
    
    @Query("SELECT p FROM CommunityPost p WHERE p.status = :status AND p.deviceType LIKE %:deviceType% AND p.faultType LIKE %:faultType%")
    Page<CommunityPost> findByStatusAndDeviceTypeContainingAndFaultTypeContaining(
            @Param("status") String status,
            @Param("deviceType") String deviceType,
            @Param("faultType") String faultType,
            Pageable pageable);
    
    @Query("SELECT p FROM CommunityPost p WHERE p.status = :status AND p.deviceType LIKE %:deviceType%")
    Page<CommunityPost> findByStatusAndDeviceTypeContaining(
            @Param("status") String status,
            @Param("deviceType") String deviceType,
            Pageable pageable);
    
    @Query("SELECT p FROM CommunityPost p WHERE p.status = :status AND p.faultType LIKE %:faultType%")
    Page<CommunityPost> findByStatusAndFaultTypeContaining(
            @Param("status") String status,
            @Param("faultType") String faultType,
            Pageable pageable);
}
