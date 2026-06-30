package com.repair.controller;

import com.repair.dto.ApiResponse;
import com.repair.entity.User;
import com.repair.service.KnowledgeService;
import org.springframework.http.ResponseEntity;
import org.springframework.security.core.annotation.AuthenticationPrincipal;
import org.springframework.web.bind.annotation.*;

import java.util.Map;

@RestController
@RequestMapping("/api/knowledge")
public class KnowledgeController {

    private final KnowledgeService service;

    public KnowledgeController(KnowledgeService service) {
        this.service = service;
    }

    @PostMapping("/add")
    public ResponseEntity<ApiResponse> add(@AuthenticationPrincipal User user,
            @RequestBody Map<String, String> body) {
        return ResponseEntity.ok(ApiResponse.ok(
                service.add(user,
                        body.get("title"),
                        body.get("content"),
                        body.get("category"),
                        body.get("device_type"))));
    }

    @GetMapping("/list")
    public ResponseEntity<ApiResponse> list(
            @RequestParam(defaultValue = "") String category,
            @RequestParam(defaultValue = "") String device_type,
            @RequestParam(defaultValue = "") String status) {
        return ResponseEntity.ok(ApiResponse.ok(
                service.list(
                        category.isEmpty() ? null : category,
                        device_type.isEmpty() ? null : device_type,
                        status.isEmpty() ? null : status)));
    }

    @GetMapping("/{id}")
    public ResponseEntity<ApiResponse> get(@PathVariable Integer id) {
        return ResponseEntity.ok(ApiResponse.ok(service.getById(id)));
    }

    @GetMapping("/{id}/chunks")
    public ResponseEntity<ApiResponse> getChunks(@PathVariable Integer id) {
        return ResponseEntity.ok(ApiResponse.ok(service.getChunks(id)));
    }

    @PostMapping("/{id}/approve")
    public ResponseEntity<ApiResponse> approve(@PathVariable Integer id) {
        return ResponseEntity.ok(ApiResponse.ok(service.approve(id)));
    }
}
