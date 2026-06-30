package com.repair.client;

import org.springframework.beans.factory.annotation.Value;
import org.springframework.core.io.ByteArrayResource;
import org.springframework.http.*;
import org.springframework.stereotype.Component;
import org.springframework.util.LinkedMultiValueMap;
import org.springframework.util.MultiValueMap;
import org.springframework.web.client.RestTemplate;

import java.util.Map;
import java.util.HashMap;

@Component
public class PythonClient {

    private final RestTemplate rest;
    private final String baseUrl;

    public PythonClient(@Value("${repair.python.base-url}") String baseUrl) {
        this.baseUrl = baseUrl;
        this.rest = new RestTemplate();
    }

    // ===== 知识检索 =====
    public Map<String, Object> retrieve(Map<String, Object> params) {
        return post("/api/v1/retrieve", params);
    }

    // ===== 检修方案 =====
    public Map<String, Object> getWorkflow(Map<String, Object> params) {
        return post("/api/v1/guidance/workflow", params);
    }

    // ===== 图片分析 =====
    public Map<String, Object> analyzeImage(byte[] imageBytes, String filename, String prompt) {
        HttpHeaders headers = new HttpHeaders();
        headers.setContentType(MediaType.MULTIPART_FORM_DATA);

        MultiValueMap<String, Object> body = new LinkedMultiValueMap<>();
        ByteArrayResource resource = new ByteArrayResource(imageBytes) {
            @Override
            public String getFilename() { return filename; }
        };
        body.add("image", resource);
        if (prompt != null && !prompt.isEmpty()) {
            body.add("prompt", prompt);
        }

        HttpEntity<MultiValueMap<String, Object>> entity = new HttpEntity<>(body, headers);
        ResponseEntity<Map> resp = rest.postForEntity(baseUrl + "/api/v1/vision/analyze", entity, Map.class);
        return resp.getBody();
    }

    // ===== 语音转文字 =====
    public Map<String, Object> speechToText(byte[] audioBytes, String filename) {
        HttpHeaders headers = new HttpHeaders();
        headers.setContentType(MediaType.MULTIPART_FORM_DATA);

        MultiValueMap<String, Object> body = new LinkedMultiValueMap<>();
        ByteArrayResource resource = new ByteArrayResource(audioBytes) {
            @Override
            public String getFilename() { return filename; }
        };
        body.add("audio", resource);

        HttpEntity<MultiValueMap<String, Object>> entity = new HttpEntity<>(body, headers);
        ResponseEntity<Map> resp = rest.postForEntity(baseUrl + "/api/v1/speech/stt", entity, Map.class);
        return resp.getBody();
    }

    // ===== AI 对话 =====
    public Map<String, Object> chat(Map<String, Object> params) {
        return post("/api/v1/chat-json", params);
    }

    @SuppressWarnings("unchecked")
    private Map<String, Object> post(String path, Map<String, Object> body) {
        HttpHeaders headers = new HttpHeaders();
        headers.setContentType(MediaType.APPLICATION_JSON);
        HttpEntity<Map<String, Object>> entity = new HttpEntity<>(body, headers);
        ResponseEntity<Map> resp = rest.postForEntity(baseUrl + path, entity, Map.class);
        return resp.getBody();
    }
}
