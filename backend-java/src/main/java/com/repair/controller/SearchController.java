package com.repair.controller;

import com.repair.client.PythonClient;
import com.repair.dto.ApiResponse;
import org.springframework.http.ResponseEntity;
import org.springframework.web.bind.annotation.*;
import org.springframework.web.multipart.MultipartFile;

import java.util.Map;
import java.util.HashMap;

@RestController
@RequestMapping("/api/search")
public class SearchController {

    private final PythonClient pythonClient;

    public SearchController(PythonClient pythonClient) {
        this.pythonClient = pythonClient;
    }

    @PostMapping("/text")
    public ResponseEntity<ApiResponse> textSearch(@RequestParam String query,
            @RequestParam(defaultValue = "10") int k) {
        Map<String, Object> params = new HashMap<>();
        params.put("query", query);
        params.put("top_k", k);
        params.put("include_images", true);
        Map<String, Object> result = pythonClient.retrieve(params);
        return ResponseEntity.ok(ApiResponse.ok(result));
    }

    @PostMapping("/image")
    public ResponseEntity<ApiResponse> imageSearch(@RequestParam("image") MultipartFile image) {
        try {
            Map<String, Object> result = pythonClient.analyzeImage(
                    image.getBytes(), image.getOriginalFilename(), "");
            return ResponseEntity.ok(ApiResponse.ok(result));
        } catch (Exception e) {
            return ResponseEntity.badRequest().body(ApiResponse.error(400, e.getMessage()));
        }
    }

    @PostMapping("/hybrid")
    public ResponseEntity<ApiResponse> hybridSearch(
            @RequestParam(required = false) String query,
            @RequestParam(value = "image", required = false) MultipartFile image,
            @RequestParam(defaultValue = "10") int k) {
        Map<String, Object> params = new HashMap<>();
        params.put("query", query != null ? query : "");
        params.put("top_k", k);
        params.put("include_images", true);
        Map<String, Object> result = pythonClient.retrieve(params);
        return ResponseEntity.ok(ApiResponse.ok(result));
    }

    @GetMapping("/suggest")
    public ResponseEntity<ApiResponse> suggest(@RequestParam String query) {
        Map<String, Object> params = new HashMap<>();
        params.put("query", query);
        params.put("top_k", 5);
        Map<String, Object> result = pythonClient.retrieve(params);
        return ResponseEntity.ok(ApiResponse.ok(result));
    }
}
