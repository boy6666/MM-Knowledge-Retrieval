package com.repair.controller;

import com.repair.dto.ApiResponse;
import com.repair.dto.LoginRequest;
import com.repair.dto.RegisterRequest;
import com.repair.service.AuthService;
import org.springframework.http.ResponseEntity;
import org.springframework.web.bind.annotation.*;

import javax.validation.Valid;

@RestController
@RequestMapping("/api/auth")
public class AuthController {

    private final AuthService authService;

    public AuthController(AuthService authService) {
        this.authService = authService;
    }

    @PostMapping("/register")
    public ResponseEntity<ApiResponse> register(@Valid @RequestBody RegisterRequest req) {
        try {
            return ResponseEntity.ok(ApiResponse.ok("注册成功", authService.register(req)));
        } catch (RuntimeException e) {
            return ResponseEntity.badRequest().body(ApiResponse.error(400, e.getMessage()));
        }
    }

    @PostMapping("/token")
    public ResponseEntity<ApiResponse> login(@Valid @RequestBody LoginRequest req) {
        try {
            return ResponseEntity.ok(ApiResponse.ok("登录成功", authService.login(req)));
        } catch (RuntimeException e) {
            return ResponseEntity.badRequest().body(ApiResponse.error(400, e.getMessage()));
        }
    }
}
