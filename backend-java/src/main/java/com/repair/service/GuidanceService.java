package com.repair.service;

import com.repair.client.PythonClient;
import com.repair.entity.Guidance;
import com.repair.entity.User;
import com.repair.repository.GuidanceRepository;
import org.springframework.data.domain.Page;
import org.springframework.data.domain.PageRequest;
import org.springframework.data.domain.Pageable;
import org.springframework.stereotype.Service;

import java.time.LocalDateTime;
import java.util.Map;
import java.util.HashMap;

@Service
public class GuidanceService {

    private final GuidanceRepository repo;
    private final PythonClient pythonClient;

    public GuidanceService(GuidanceRepository repo, PythonClient pythonClient) {
        this.repo = repo;
        this.pythonClient = pythonClient;
    }

    @SuppressWarnings("unchecked")
    public Map<String, Object> generate(User user, String deviceType, String faultType) {
        Map<String, Object> params = new HashMap<>();
        params.put("device_type", deviceType != null ? deviceType : "");
        params.put("fault_type", faultType != null ? faultType : "");
        params.put("user_id", user != null ? user.getId() : 0);
        Map<String, Object> result = pythonClient.getWorkflow(params);
        // Python 返回格式：{title, content, guidance_id, ...} 无 {code,data} 包装
        if (result != null && result.containsKey("title")) {
            // 自动保存草稿
            Guidance g = new Guidance();
            g.setTitle((String) result.getOrDefault("title", deviceType + " - " + faultType));
            g.setDeviceType(deviceType);
            g.setFaultType(faultType);
            g.setContent((String) result.getOrDefault("content", ""));
            g.setAuthorId(user.getId());
            g.setStatus("draft");
            g.setCreatedAt(LocalDateTime.now());
            g.setUpdatedAt(LocalDateTime.now());
            repo.save(g);
            result.put("guidance_id", g.getId());
            return result;
        }
        return result;
    }

    public Map<String, Object> generateFromChat(User user, String conversationId, Integer messageId) {
        Guidance g = new Guidance();
        g.setTitle("AI对话方案");
        g.setAuthorId(user.getId());
        g.setStatus("draft");
        g.setSourceType("chat_generated");
        g.setSourceId(conversationId);
        g.setCreatedAt(LocalDateTime.now());
        g.setUpdatedAt(LocalDateTime.now());
        repo.save(g);
        Map<String, Object> result = new HashMap<>();
        result.put("guidance_id", g.getId());
        result.put("title", g.getTitle());
        result.put("content", "请先与AI对话，AI将根据对话内容生成检修方案。");
        return result;
    }

    public Map<String, Object> save(User user, Map<String, Object> body) {
        Guidance g = new Guidance();
        g.setTitle((String) body.getOrDefault("title", ""));
        g.setDeviceType((String) body.getOrDefault("device_type", ""));
        g.setFaultType((String) body.getOrDefault("fault_type", ""));
        g.setContent((String) body.getOrDefault("content", ""));
        g.setAuthorId(user.getId());
        if (body.containsKey("is_public")) {
            g.setIsPublic((Boolean) body.get("is_public"));
        }
        g.setCreatedAt(LocalDateTime.now());
        g.setUpdatedAt(LocalDateTime.now());
        Guidance saved = repo.save(g);
        Map<String, Object> result = new HashMap<>();
        result.put("guidance_id", saved.getId());
        result.put("id", saved.getId());
        result.put("title", saved.getTitle());
        result.put("content", saved.getContent());
        result.put("device_type", saved.getDeviceType());
        result.put("fault_type", saved.getFaultType());
        return result;
    }

    public Guidance getById(Integer id) {
        Guidance g = repo.findById(id).orElseThrow(() -> new RuntimeException("方案不存在"));
        g.setViews(g.getViews() + 1);
        repo.save(g);
        return g;
    }

    public Map<String, Object> listMine(User user, int page, int size) {
        Pageable pageable = PageRequest.of(page - 1, size);
        return pageResult(repo.findByAuthorId(user.getId(), pageable));
    }

    public Map<String, Object> listPublic(String deviceType, String faultType,
            String keyword, int page, int size) {
        Pageable pageable = PageRequest.of(page - 1, size);
        Page<Guidance> result;
        if (deviceType != null && !deviceType.isEmpty()) {
            result = repo.findByIsPublicTrueAndDeviceType(true, deviceType, pageable);
        } else if (faultType != null && !faultType.isEmpty()) {
            result = repo.findByIsPublicTrueAndFaultType(true, faultType, pageable);
        } else {
            result = repo.findByIsPublicTrue(pageable);
        }
        return pageResult(result);
    }

    public void delete(User user, Integer id) {
        Guidance g = repo.findById(id).orElseThrow(() -> new RuntimeException("方案不存在"));
        if (!g.getAuthorId().equals(user.getId()) && !"admin".equals(user.getRole())) {
            throw new RuntimeException("无权删除");
        }
        repo.delete(g);
    }

    public Guidance togglePublic(User user, Integer id) {
        Guidance g = repo.findById(id).orElseThrow(() -> new RuntimeException("方案不存在"));
        if (!g.getAuthorId().equals(user.getId())) {
            throw new RuntimeException("无权操作");
        }
        g.setIsPublic(!g.getIsPublic());
        g.setUpdatedAt(LocalDateTime.now());
        return repo.save(g);
    }

    private Map<String, Object> pageResult(Page<?> page) {
        Map<String, Object> result = new HashMap<>();
        result.put("items", page.getContent());
        result.put("total", page.getTotalElements());
        result.put("page", page.getNumber() + 1);
        result.put("size", page.getSize());
        result.put("pages", page.getTotalPages());
        return result;
    }
}
