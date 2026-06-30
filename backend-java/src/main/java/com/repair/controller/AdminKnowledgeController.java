package com.repair.controller;

import com.repair.dto.ApiResponse;
import com.repair.entity.User;
import com.repair.service.KnowledgeService;
import org.springframework.http.ResponseEntity;
import org.springframework.security.core.annotation.AuthenticationPrincipal;
import org.springframework.web.bind.annotation.*;

import java.util.Map;
import java.util.HashMap;

@RestController
@RequestMapping("/api/admin")
public class AdminKnowledgeController {

    private final KnowledgeService knowledgeService;

    public AdminKnowledgeController(KnowledgeService knowledgeService) {
        this.knowledgeService = knowledgeService;
    }

    @PostMapping("/knowledge/{id}/reject")
    public ResponseEntity<ApiResponse> rejectKnowledge(@PathVariable Integer id) {
        knowledgeService.reject(id);
        Map<String, Object> msg = new HashMap<>();
        msg.put("message", "已驳回");
        return ResponseEntity.ok(ApiResponse.ok(msg));
    }

    @DeleteMapping("/knowledge/{id}")
    public ResponseEntity<ApiResponse> deleteKnowledge(@PathVariable Integer id) {
        knowledgeService.delete(id);
        Map<String, Object> msg2 = new HashMap<>();
        msg2.put("message", "已删除");
        return ResponseEntity.ok(ApiResponse.ok(msg2));
    }
}
