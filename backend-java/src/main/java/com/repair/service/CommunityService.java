package com.repair.service;

import com.repair.client.PythonClient;
import com.repair.entity.CommunityPost;
import com.repair.entity.User;
import com.repair.repository.CommunityPostRepository;
import org.springframework.data.domain.Page;
import org.springframework.data.domain.PageRequest;
import org.springframework.data.domain.Pageable;
import org.springframework.stereotype.Service;

import java.time.LocalDateTime;
import java.util.*;
import java.util.Map;
import java.util.HashMap;

@Service
public class CommunityService {

    private final CommunityPostRepository repo;
    private final PythonClient pythonClient;

    public CommunityService(CommunityPostRepository repo, PythonClient pythonClient) {
        this.repo = repo;
        this.pythonClient = pythonClient;
    }

    public CommunityPost create(User user, String title, String deviceType,
            String faultType, String content, String images) {
        CommunityPost post = new CommunityPost();
        post.setTitle(title);
        post.setDeviceType(deviceType);
        post.setFaultType(faultType);
        post.setContent(content);
        post.setImages(images);
        post.setAuthorId(user.getId());
        post.setAuthorName(user.getUsername());
        post.setStatus("pending");
        post.setCreatedAt(LocalDateTime.now());

        // 调用 Python 算法层匹配章节
        try {
            Map<String, Object> searchParams = new HashMap<>();
            searchParams.put("query", title + " " + faultType + " " + content.substring(0, Math.min(200, content.length())));
            searchParams.put("top_k", 1);
            Map<String, Object> searchResult = pythonClient.retrieve(searchParams);
            if (searchResult != null && searchResult.get("results") instanceof List) {
                List<?> results = (List<?>) searchResult.get("results");
                if (!results.isEmpty()) {
                    Object first = results.get(0);
                    if (first instanceof Map) {
                        Object chapterTitle = ((Map<?, ?>) first).get("title");
                        if (chapterTitle != null) {
                            post.setMatchedChapter((String) chapterTitle);
                        }
                    }
                }
            }
        } catch (Exception ignored) {}

        return repo.save(post);
    }

    public Map<String, Object> listApproved(String deviceType, String faultType, String keyword, int page, int size) {
        // 先获取所有approved帖子，不限制数量
        List<CommunityPost> all = new ArrayList<>(repo.findByStatus("approved", PageRequest.of(0, Integer.MAX_VALUE)).getContent());
        
        List<CommunityPost> filtered = all;
        
        if (deviceType != null && !deviceType.isEmpty()) {
            filtered = filtered.stream()
                    .filter(p -> p.getDeviceType() != null && p.getDeviceType().contains(deviceType))
                    .collect(java.util.stream.Collectors.toList());
        }
        if (faultType != null && !faultType.isEmpty()) {
            filtered = filtered.stream()
                    .filter(p -> p.getFaultType() != null && matchesFaultType(p.getFaultType(), faultType))
                    .collect(java.util.stream.Collectors.toList());
        }
        
        // 分页
        int total = filtered.size();
        int fromIndex = (page - 1) * size;
        int toIndex = Math.min(fromIndex + size, total);
        List<CommunityPost> paged = fromIndex < total ? filtered.subList(fromIndex, toIndex) : new ArrayList<>();
        
        Map<String, Object> result = new HashMap<>();
        result.put("items", paged);
        result.put("total", total);
        result.put("page", page);
        result.put("size", size);
        result.put("pages", (total + size - 1) / size);
        return result;
    }
    
    private boolean matchesFaultType(String postFaultType, String searchFaultType) {
        if (postFaultType == null || searchFaultType == null) {
            return false;
        }
        if (postFaultType.contains(searchFaultType)) {
            return true;
        }
        String normalizedSearch = removeVerbsAndNumbers(searchFaultType);
        String normalizedPost = removeVerbsAndNumbers(postFaultType);
        if (normalizedPost.contains(normalizedSearch)) {
            return true;
        }
        for (int i = 0; i <= normalizedSearch.length() - 2; i++) {
            String twoChar = normalizedSearch.substring(i, i + 2);
            if (normalizedPost.contains(twoChar)) {
                return true;
            }
        }
        return false;
    }
    
    private String removeVerbsAndNumbers(String str) {
        if (str == null) return "";
        String result = str.replace("拆卸", "")
                          .replace("安装", "")
                          .replace("更换", "")
                          .replace("检查", "")
                          .replace("维修", "")
                          .replace("清洗", "")
                          .replace("调整", "")
                          .replace("测试", "")
                          .replace("保养", "")
                          .replace("与", "")
                          .replace("/", "")
                          .replace("-", "");
        return result.replaceAll("\\d+", "");
    }

    public CommunityPost getById(Integer id) {
        CommunityPost post = repo.findById(id).orElseThrow(() -> new RuntimeException("帖子不存在"));
        post.setViews(post.getViews() + 1);
        repo.save(post);
        return post;
    }

    public Map<String, Object> listMyPosts(User user, int page, int size) {
        Pageable pageable = PageRequest.of(page - 1, size);
        return pageResult(repo.findByAuthorId(user.getId(), pageable));
    }

    public CommunityPost like(User user, Integer postId) {
        CommunityPost post = repo.findById(postId).orElseThrow(() -> new RuntimeException("帖子不存在"));
        String likedUsers = post.getLikedUsers();
        List<Integer> liked = parseJsonArray(likedUsers);
        if (liked.contains(user.getId())) {
            liked.remove(user.getId());
            post.setLikes(Math.max(0, post.getLikes() - 1));
        } else {
            liked.add(user.getId());
            post.setLikes(post.getLikes() + 1);
        }
        post.setLikedUsers(liked.toString());
        return repo.save(post);
    }

    public void delete(User user, Integer postId) {
        CommunityPost post = repo.findById(postId).orElseThrow(() -> new RuntimeException("帖子不存在"));
        if (!post.getAuthorId().equals(user.getId())) {
            throw new RuntimeException("只能删除自己的帖子");
        }
        repo.delete(post);
    }

    // Admin
    public Map<String, Object> listPending(int page, int size) {
        Pageable pageable = PageRequest.of(page - 1, size);
        return pageResult(repo.findByStatus("pending", pageable));
    }

    public CommunityPost approve(User admin, Integer postId) {
        CommunityPost post = repo.findById(postId).orElseThrow(() -> new RuntimeException("帖子不存在"));
        post.setStatus("approved");
        post.setReviewedAt(LocalDateTime.now());
        post.setReviewerId(admin.getId());
        return repo.save(post);
    }

    public CommunityPost reject(User admin, Integer postId, String comment) {
        CommunityPost post = repo.findById(postId).orElseThrow(() -> new RuntimeException("帖子不存在"));
        post.setStatus("rejected");
        post.setReviewedAt(LocalDateTime.now());
        post.setReviewerId(admin.getId());
        post.setReviewComment(comment);
        return repo.save(post);
    }

    @SuppressWarnings("unchecked")
    private List<Integer> parseJsonArray(String json) {
        try {
            String trimmed = json.trim();
            if (trimmed.startsWith("[") && trimmed.endsWith("]")) {
                if (trimmed.length() <= 2) return new ArrayList<>();
                String[] parts = trimmed.substring(1, trimmed.length() - 1).split(",");
                List<Integer> list = new ArrayList<>();
                for (String p : parts) {
                    list.add(Integer.parseInt(p.trim()));
                }
                return list;
            }
        } catch (Exception ignored) {}
        return new ArrayList<>();
    }

    private Map<String, Object> pageResult(Page<CommunityPost> page) {
        Map<String, Object> result = new HashMap<>();
        result.put("items", page.getContent());
        result.put("total", page.getTotalElements());
        result.put("page", page.getNumber() + 1);
        result.put("size", page.getSize());
        result.put("pages", page.getTotalPages());
        return result;
    }
}
