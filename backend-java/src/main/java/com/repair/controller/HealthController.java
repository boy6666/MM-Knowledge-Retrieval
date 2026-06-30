package com.repair.controller;

import com.repair.dto.ApiResponse;
import org.springframework.web.bind.annotation.GetMapping;
import org.springframework.web.bind.annotation.RestController;

import java.util.Map;
import java.util.HashMap;

@RestController
public class HealthController {

    @GetMapping("/health")
    public ApiResponse health() {
        Map<String, Object> data = new HashMap<>();
        data.put("status", "healthy");
        data.put("service", "repair-backend-java");
        return ApiResponse.ok(data);
    }
}
