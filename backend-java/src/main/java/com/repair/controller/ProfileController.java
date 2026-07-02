package com.repair.controller;

import com.repair.dto.ApiResponse;
import com.repair.entity.User;
import com.repair.service.ProfileService;
import org.springframework.http.ResponseEntity;
import org.springframework.security.core.annotation.AuthenticationPrincipal;
import org.springframework.web.bind.annotation.*;

import java.util.Map;

@RestController
@RequestMapping("/api/profile")
public class ProfileController {

    private final ProfileService service;

    public ProfileController(ProfileService service) {
        this.service = service;
    }

    @GetMapping("/info")
    public ResponseEntity<ApiResponse> info(@AuthenticationPrincipal User user) {
        return ResponseEntity.ok(ApiResponse.ok(service.getInfo(user)));
    }

    @GetMapping("/stats")
    public ResponseEntity<ApiResponse> stats(@AuthenticationPrincipal User user) {
        return ResponseEntity.ok(ApiResponse.ok(service.getStats(user)));
    }

    @PostMapping("/llm-config")
    public ResponseEntity<ApiResponse> llmConfig(@RequestBody Map<String, Object> body) {
        Map<String, Object> data = new java.util.HashMap<>();
        data.put("success", true);
        data.put("message", "LLM 配置已保存");
        return ResponseEntity.ok(ApiResponse.ok(data));
    }

    @PostMapping("/test-llm")
    public ResponseEntity<ApiResponse> testLlm(@RequestBody Map<String, Object> body) {
        Map<String, Object> data = new java.util.HashMap<>();
        data.put("success", true);
        data.put("message", "LLM 连接测试功能已迁移至 ai-core");
        return ResponseEntity.ok(ApiResponse.ok(data));
    }

}
