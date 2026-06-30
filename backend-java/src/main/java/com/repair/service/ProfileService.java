package com.repair.service;

import com.repair.client.PythonClient;
import com.repair.entity.User;
import com.repair.repository.*;
import org.springframework.stereotype.Service;

import java.util.*;

@Service
public class ProfileService {

    private final CommunityPostRepository postRepo;
    private final GuidanceRepository guidanceRepo;
    public ProfileService(CommunityPostRepository postRepo,
            GuidanceRepository guidanceRepo) {
        this.postRepo = postRepo;
        this.guidanceRepo = guidanceRepo;
    }

    public Map<String, Object> getInfo(User user) {
        Map<String, Object> info = new HashMap<>();
        info.put("id", user.getId());
        info.put("username", user.getUsername());
        info.put("email", user.getEmail());
        info.put("role", user.getRole());
        info.put("created_at", user.getCreatedAt());
        return info;
    }

    public Map<String, Object> getStats(User user) {
        Map<String, Object> stats = new HashMap<>();
        stats.put("guidance_count", guidanceRepo.count());
        stats.put("post_count", postRepo.count());
        return stats;
    }


}
