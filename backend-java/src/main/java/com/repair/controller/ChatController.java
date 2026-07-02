package com.repair.controller;

import com.repair.client.PythonClient;
import com.repair.dto.ApiResponse;
import org.springframework.http.ResponseEntity;
import org.springframework.web.bind.annotation.*;
import org.springframework.web.multipart.MultipartFile;

import java.util.Map;
import java.util.HashMap;
import java.util.UUID;

@RestController
@RequestMapping("/api/chat")
public class ChatController {

    private final PythonClient pythonClient;

    public ChatController(PythonClient pythonClient) {
        this.pythonClient = pythonClient;
    }

    @PostMapping("/new")
    public ResponseEntity<ApiResponse> newConversation() {
        Map<String, Object> data = new HashMap<>();
        data.put("conversation_id", UUID.randomUUID().toString());
        data.put("message_count", 0);
        return ResponseEntity.ok(ApiResponse.ok(data));
    }

    @GetMapping("/{conversationId}")
    public ResponseEntity<ApiResponse> getConversation(@PathVariable String conversationId) {
        Map<String, Object> data = new HashMap<>();
        data.put("conversation_id", conversationId);
        data.put("messages", new Object[]{});
        return ResponseEntity.ok(ApiResponse.ok(data));
    }

    @PostMapping("/{conversationId}/chat")
    public ResponseEntity<ApiResponse> chat(
            @PathVariable String conversationId,
            @RequestParam(value = "message", required = false) String message,
            @RequestParam(value = "image", required = false) MultipartFile image,
            @RequestParam(value = "video", required = false) MultipartFile video,
            @RequestParam(value = "audio", required = false) MultipartFile audio) {

        String fullMessage = message != null ? message : "";
        String mediaType = "text";

        // 如果有图片，走 ai-core 的视觉分析
        if (image != null && !image.isEmpty()) {
            try {
                mediaType = "image";
                Map<String, Object> analysis = pythonClient.analyzeImage(
                        image.getBytes(), image.getOriginalFilename(),
                        "请描述这张图片中的设备状态和可能的故障");
                if (analysis.containsKey("description")) {
                    fullMessage = (fullMessage + " [图片分析]: " + analysis.get("description")).trim();
                }
            } catch (Exception e) {
                fullMessage = (fullMessage + " [图片上传]").trim();
            }
        }

        // 调用 ai-core 对话
        Map<String, Object> params = new HashMap<>();
        params.put("message", fullMessage);
        params.put("conversation_id", conversationId);
        params.put("media_type", mediaType);
        Map<String, Object> result = pythonClient.chat(params);

        return ResponseEntity.ok(ApiResponse.ok(result));
    }

    @DeleteMapping("/{conversationId}")
    public ResponseEntity<ApiResponse> deleteConversation(@PathVariable String conversationId) {
        Map<String, Object> msg = new HashMap<>();
        msg.put("message", "对话已删除");
        return ResponseEntity.ok(ApiResponse.ok(msg));
    }

    @PostMapping("/speech-to-text")
    public ResponseEntity<ApiResponse> speechToText(@RequestParam("audio") MultipartFile audio) {
        try {
            Map<String, Object> result = pythonClient.speechToText(
                    audio.getBytes(), audio.getOriginalFilename());
            return ResponseEntity.ok(ApiResponse.ok(result));
        } catch (Exception e) {
            return ResponseEntity.badRequest().body(ApiResponse.error(400, e.getMessage()));
        }
    }

    @PostMapping("/video-analyze")
    public ResponseEntity<ApiResponse> videoAnalyze(@RequestParam("video") MultipartFile video) {
        Map<String, Object> data = new HashMap<>();
        data.put("description", "视频分析功能需要 ai-core 的视频帧处理模块。");
        data.put("query", "");
        return ResponseEntity.ok(ApiResponse.ok(data));
    }

    @PostMapping("/image-generate")
    public ResponseEntity<ApiResponse> imageGenerate(@RequestParam String prompt) {
        Map<String, Object> data = new HashMap<>();
        data.put("prompt", prompt);
        data.put("image_url", "https://picsum.photos/seed/" + prompt.hashCode() + "/800/600");
        return ResponseEntity.ok(ApiResponse.ok(data));
    }
}
