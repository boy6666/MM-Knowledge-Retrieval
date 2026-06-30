package com.repair.service;

import com.repair.client.PythonClient;
import com.repair.entity.KnowledgeItem;
import com.repair.entity.User;
import com.repair.repository.KnowledgeRepository;
import org.springframework.stereotype.Service;

import java.time.LocalDateTime;
import java.util.*;

@Service
public class KnowledgeService {

    private final KnowledgeRepository repo;
    public KnowledgeService(KnowledgeRepository repo) {
        this.repo = repo;
    }

    public KnowledgeItem add(User user, String title, String content,
            String category, String deviceType) {
        KnowledgeItem item = new KnowledgeItem();
        item.setTitle(title);
        item.setContent(content);
        item.setCategory(category != null ? category : "");
        item.setDeviceType(deviceType != null ? deviceType : "");
        item.setAuthorId(user.getId());
        item.setStatus("pending");
        item.setCreatedAt(LocalDateTime.now());
        return repo.save(item);
    }

    public List<KnowledgeItem> list(String category, String deviceType, String status) {
        if (status != null && !status.isEmpty()) {
            return repo.findByStatus(status);
        }
        if (category != null && !category.isEmpty()) {
            return repo.findByCategory(category);
        }
        if (deviceType != null && !deviceType.isEmpty()) {
            return repo.findByDeviceType(deviceType);
        }
        return repo.findAll();
    }

    public KnowledgeItem getById(Integer id) {
        return repo.findById(id).orElseThrow(() -> new RuntimeException("知识条目不存在"));
    }

    public KnowledgeItem approve(Integer id) {
        KnowledgeItem item = repo.findById(id).orElseThrow(() -> new RuntimeException("知识条目不存在"));
        item.setStatus("approved");
        return repo.save(item);
    }

    public void reject(Integer id) {
        KnowledgeItem item = repo.findById(id).orElseThrow(() -> new RuntimeException("知识条目不存在"));
        item.setStatus("rejected");
        repo.save(item);
    }

    public void delete(Integer id) {
        repo.deleteById(id);
    }

    public Map<String, Object> getChunks(Integer id) {
        Map<String, Object> result = new HashMap<>();
        result.put("chunks", new ArrayList<>());
        result.put("total", 0);
        return result;
    }
}
