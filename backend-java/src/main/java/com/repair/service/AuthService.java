package com.repair.service;

import com.repair.dto.LoginRequest;
import com.repair.dto.RegisterRequest;
import com.repair.entity.User;
import com.repair.repository.UserRepository;
import com.repair.security.JwtUtil;
import org.springframework.security.crypto.password.PasswordEncoder;
import org.springframework.stereotype.Service;

import java.util.HashMap;
import java.util.Map;

@Service
public class AuthService {

    private final UserRepository userRepo;
    private final PasswordEncoder encoder;
    private final JwtUtil jwtUtil;

    public AuthService(UserRepository userRepo, PasswordEncoder encoder, JwtUtil jwtUtil) {
        this.userRepo = userRepo;
        this.encoder = encoder;
        this.jwtUtil = jwtUtil;
    }

    public Map<String, Object> register(RegisterRequest req) {
        if (userRepo.existsByUsername(req.getUsername())) {
            throw new RuntimeException("用户名已存在");
        }
        User user = new User(req.getUsername(), encoder.encode(req.getPassword()), req.getEmail());
        userRepo.save(user);
        String token = jwtUtil.generateToken(user.getId(), user.getUsername(), user.getRole());
        Map<String, Object> result = new HashMap<>();
        result.put("access_token", token);
        result.put("token_type", "bearer");
        result.put("user_id", user.getId());
        result.put("username", user.getUsername());
        result.put("role", user.getRole());
        return result;
    }

    public Map<String, Object> login(LoginRequest req) {
        User user = userRepo.findByUsername(req.getUsername())
                .orElseThrow(() -> new RuntimeException("用户名或密码错误"));
        if (!encoder.matches(req.getPassword(), user.getPasswordHash())) {
            throw new RuntimeException("用户名或密码错误");
        }
        String token = jwtUtil.generateToken(user.getId(), user.getUsername(), user.getRole());
        Map<String, Object> result = new HashMap<>();
        result.put("access_token", token);
        result.put("token_type", "bearer");
        result.put("user_id", user.getId());
        result.put("username", user.getUsername());
        result.put("role", user.getRole());
        return result;
    }
}
