package com.repair.service;

import com.repair.entity.User;
import com.repair.repository.*;
import org.springframework.data.domain.Page;
import org.springframework.data.domain.PageRequest;
import org.springframework.stereotype.Service;

import java.util.*;

@Service
public class AdminService {

    private final UserRepository userRepo;
    private final CommunityPostRepository postRepo;
    private final GuidanceRepository guidanceRepo;

    public AdminService(UserRepository userRepo, CommunityPostRepository postRepo,
            GuidanceRepository guidanceRepo) {
        this.userRepo = userRepo;
        this.postRepo = postRepo;
        this.guidanceRepo = guidanceRepo;
    }

    public Map<String, Object> listUsers(int page, int size) {
        Page<User> users = userRepo.findAll(PageRequest.of(page - 1, size));
        Map<String, Object> result = new HashMap<>();
        result.put("items", users.getContent());
        result.put("total", users.getTotalElements());
        result.put("page", page);
        return result;
    }

    public User updateRole(Integer userId, String role) {
        User user = userRepo.findById(userId).orElseThrow(() -> new RuntimeException("用户不存在"));
        if (role != null && (role.equals("user") || role.equals("admin"))) {
            user.setRole(role);
            return userRepo.save(user);
        }
        throw new RuntimeException("无效角色");
    }

    public void deleteUser(User me, Integer userId) {
        if (me.getId().equals(userId)) {
            throw new RuntimeException("不能删除自己");
        }
        userRepo.deleteById(userId);
    }

    public Map<String, Object> stats() {
        Map<String, Object> result = new HashMap<>();
        result.put("total_users", userRepo.count());
        result.put("total_posts", postRepo.count());
        result.put("total_guidance", guidanceRepo.count());
        result.put("pending_posts", postRepo.findByStatus("pending", PageRequest.of(0, 1)).getTotalElements());
        return result;
    }
}
