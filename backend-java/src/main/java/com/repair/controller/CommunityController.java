package com.repair.controller;

import com.repair.dto.ApiResponse;
import com.repair.entity.CommunityPost;
import com.repair.entity.User;
import com.repair.service.CommunityService;
import org.springframework.http.ResponseEntity;
import org.springframework.security.core.annotation.AuthenticationPrincipal;
import org.springframework.web.bind.annotation.*;

import java.util.Map;
import java.util.HashMap;

@RestController
@RequestMapping("/api/community")
public class CommunityController {

    private final CommunityService service;

    public CommunityController(CommunityService service) {
        this.service = service;
    }

    @GetMapping("/list")
    public ResponseEntity<ApiResponse> list(
            @RequestParam(defaultValue = "") String device_type,
            @RequestParam(defaultValue = "") String fault_type,
            @RequestParam(defaultValue = "") String keyword,
            @RequestParam(defaultValue = "1") int page,
            @RequestParam(defaultValue = "10") int size) {
        return ResponseEntity.ok(ApiResponse.ok(
                service.listApproved(
                        device_type.isEmpty() ? null : device_type,
                        fault_type.isEmpty() ? null : fault_type,
                        keyword.isEmpty() ? null : keyword,
                        page, size)));
    }

    @GetMapping("/{id}")
    public ResponseEntity<ApiResponse> get(@PathVariable Integer id) {
        Map<String, Object> result = new HashMap<>();
        result.put("post", service.getById(id));
        return ResponseEntity.ok(ApiResponse.ok(result));
    }

    @PostMapping("/create")
    public ResponseEntity<ApiResponse> create(@AuthenticationPrincipal User user,
            @RequestBody Map<String, Object> body) {
        CommunityPost post = service.create(user,
                (String) body.get("title"),
                (String) body.getOrDefault("device_type", ""),
                (String) body.getOrDefault("fault_type", ""),
                (String) body.getOrDefault("content", ""),
                (String) body.getOrDefault("images", "[]"));
        return ResponseEntity.ok(ApiResponse.ok(post));
    }

    @GetMapping("/list/mine")
    public ResponseEntity<ApiResponse> listMine(@AuthenticationPrincipal User user,
            @RequestParam(defaultValue = "1") int page,
            @RequestParam(defaultValue = "10") int size) {
        return ResponseEntity.ok(ApiResponse.ok(service.listMyPosts(user, page, size)));
    }

    @PostMapping("/{id}/like")
    public ResponseEntity<ApiResponse> like(@AuthenticationPrincipal User user,
            @PathVariable Integer id) {
        return ResponseEntity.ok(ApiResponse.ok(service.like(user, id)));
    }

    @DeleteMapping("/{id}")
    public ResponseEntity<ApiResponse> delete(@AuthenticationPrincipal User user,
            @PathVariable Integer id) {
        service.delete(user, id);
        Map<String, Object> msg = new HashMap<>();
        msg.put("message", "删除成功");
        return ResponseEntity.ok(ApiResponse.ok(msg));
    }

    @GetMapping("/admin/pending")
    public ResponseEntity<ApiResponse> pending(@RequestParam(defaultValue = "1") int page,
            @RequestParam(defaultValue = "10") int size) {
        return ResponseEntity.ok(ApiResponse.ok(service.listPending(page, size)));
    }

    @PostMapping("/admin/{id}/approve")
    public ResponseEntity<ApiResponse> approve(@AuthenticationPrincipal User user,
            @PathVariable Integer id) {
        return ResponseEntity.ok(ApiResponse.ok(service.approve(user, id)));
    }

    @PostMapping("/admin/{id}/reject")
    public ResponseEntity<ApiResponse> reject(@AuthenticationPrincipal User user,
            @PathVariable Integer id, @RequestBody(required = false) Map<String, String> body) {
        String comment = body != null ? body.getOrDefault("comment", "") : "";
        return ResponseEntity.ok(ApiResponse.ok(service.reject(user, id, comment)));
    }
}
