package com.repair.controller;

import com.repair.dto.ApiResponse;
import com.repair.entity.User;
import com.repair.service.GuidanceService;
import org.springframework.http.ResponseEntity;
import org.springframework.security.core.annotation.AuthenticationPrincipal;
import org.springframework.web.bind.annotation.*;

import java.util.Map;
import java.util.HashMap;

@RestController
@RequestMapping("/api/guidance")
public class GuidanceController {

    private final GuidanceService service;

    public GuidanceController(GuidanceService service) {
        this.service = service;
    }

    // 调用算法层生成方案
    @PostMapping("/generate")
    public ResponseEntity<ApiResponse> generate(@AuthenticationPrincipal User user,
            @RequestBody Map<String, String> body) {
        return ResponseEntity.ok(ApiResponse.ok(
                service.generate(user, body.get("device_type"), body.get("fault_type"))));
    }

    // 从对话消息生成方案
    @PostMapping("/generate-from-chat")
    public ResponseEntity<ApiResponse> generateFromChat(@AuthenticationPrincipal User user,
            @RequestBody Map<String, Object> body) {
        Integer messageId = body.get("message_id") instanceof Integer
                ? (Integer) body.get("message_id") : null;
        String conversationId = (String) body.get("conversation_id");
        return ResponseEntity.ok(ApiResponse.ok(
                service.generateFromChat(user, conversationId, messageId)));
    }

    @PostMapping("/save")
    public ResponseEntity<ApiResponse> save(@AuthenticationPrincipal User user,
            @RequestBody Map<String, Object> body) {
        return ResponseEntity.ok(ApiResponse.ok(service.save(user, body)));
    }

    @GetMapping("/{id}")
    public ResponseEntity<ApiResponse> get(@PathVariable Integer id) {
        Map<String, Object> result = new HashMap<>();
        result.put("guidance", service.getById(id));
        return ResponseEntity.ok(ApiResponse.ok(result));
    }

    @GetMapping("/list/mine")
    public ResponseEntity<ApiResponse> listMine(@AuthenticationPrincipal User user,
            @RequestParam(defaultValue = "1") int page,
            @RequestParam(defaultValue = "10") int size) {
        return ResponseEntity.ok(ApiResponse.ok(service.listMine(user, page, size)));
    }

    @GetMapping("/list/public")
    public ResponseEntity<ApiResponse> listPublic(
            @RequestParam(defaultValue = "") String device_type,
            @RequestParam(defaultValue = "") String fault_type,
            @RequestParam(defaultValue = "") String keyword,
            @RequestParam(defaultValue = "1") int page,
            @RequestParam(defaultValue = "10") int size) {
        return ResponseEntity.ok(ApiResponse.ok(
                service.listPublic(
                        device_type.isEmpty() ? null : device_type,
                        fault_type.isEmpty() ? null : fault_type,
                        keyword.isEmpty() ? null : keyword,
                        page, size)));
    }

    @DeleteMapping("/{id}")
    public ResponseEntity<ApiResponse> delete(@AuthenticationPrincipal User user,
            @PathVariable Integer id) {
        service.delete(user, id);
        Map<String, Object> msg = new HashMap<>();
        msg.put("message", "删除成功");
        return ResponseEntity.ok(ApiResponse.ok(msg));
    }

    @PostMapping("/{id}/public")
    public ResponseEntity<ApiResponse> togglePublic(@AuthenticationPrincipal User user,
            @PathVariable Integer id) {
        return ResponseEntity.ok(ApiResponse.ok(service.togglePublic(user, id)));
    }
}
