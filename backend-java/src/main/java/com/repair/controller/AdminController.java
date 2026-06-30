package com.repair.controller;

import com.repair.dto.ApiResponse;
import com.repair.entity.User;
import com.repair.service.AdminService;
import org.springframework.http.ResponseEntity;
import org.springframework.security.core.annotation.AuthenticationPrincipal;
import org.springframework.web.bind.annotation.*;

import java.util.Map;
import java.util.HashMap;

@RestController
@RequestMapping("/api/admin")
public class AdminController {

    private final AdminService service;

    public AdminController(AdminService service) {
        this.service = service;
    }

    @GetMapping("/users")
    public ResponseEntity<ApiResponse> listUsers(@RequestParam(defaultValue = "1") int page,
            @RequestParam(defaultValue = "20") int size) {
        return ResponseEntity.ok(ApiResponse.ok(service.listUsers(page, size)));
    }

    @PostMapping("/users/{id}/role")
    public ResponseEntity<ApiResponse> updateRole(@PathVariable Integer id,
            @RequestBody Map<String, String> body) {
        return ResponseEntity.ok(ApiResponse.ok(service.updateRole(id, body.get("role"))));
    }

    @DeleteMapping("/users/{id}")
    public ResponseEntity<ApiResponse> deleteUser(@AuthenticationPrincipal User me,
            @PathVariable Integer id) {
        service.deleteUser(me, id);
        Map<String, Object> msg = new HashMap<>();
        msg.put("message", "删除成功");
        return ResponseEntity.ok(ApiResponse.ok(msg));
    }

    @GetMapping("/stats")
    public ResponseEntity<ApiResponse> stats() {
        return ResponseEntity.ok(ApiResponse.ok(service.stats()));
    }
}
