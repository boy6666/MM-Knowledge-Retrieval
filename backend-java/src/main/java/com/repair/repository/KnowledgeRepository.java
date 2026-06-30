package com.repair.repository;

import com.repair.entity.KnowledgeItem;
import org.springframework.data.jpa.repository.JpaRepository;
import java.util.List;

public interface KnowledgeRepository extends JpaRepository<KnowledgeItem, Integer> {
    List<KnowledgeItem> findByStatus(String status);
    List<KnowledgeItem> findByCategory(String category);
    List<KnowledgeItem> findByDeviceType(String deviceType);
}
