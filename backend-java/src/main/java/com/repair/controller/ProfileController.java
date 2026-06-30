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


}
