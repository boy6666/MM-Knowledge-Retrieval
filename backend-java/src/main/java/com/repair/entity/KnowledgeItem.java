package com.repair.entity;

import javax.persistence.*;
import java.time.LocalDateTime;

@Entity
@Table(name = "knowledge_items")
public class KnowledgeItem {
    @Id
    @GeneratedValue(strategy = GenerationType.IDENTITY)
    private Integer id;

    @Column(nullable = false)
    private String title;

    @Column(columnDefinition = "text")
    private String content = "";

    private String category = "";

    @Column(name = "device_type")
    private String deviceType = "";

    private String status = "pending";

    private String source = "manual_upload";

    @Column(name = "author_id")
    private Integer authorId;

    @Column(name = "created_at")
    private LocalDateTime createdAt = LocalDateTime.now();

    public KnowledgeItem() {}

    public Integer getId() { return id; }
    public void setId(Integer id) { this.id = id; }
    public String getTitle() { return title; }
    public void setTitle(String title) { this.title = title; }
    public String getContent() { return content; }
    public void setContent(String content) { this.content = content; }
    public String getCategory() { return category; }
    public void setCategory(String category) { this.category = category; }
    public String getDeviceType() { return deviceType; }
    public void setDeviceType(String deviceType) { this.deviceType = deviceType; }
    public String getStatus() { return status; }
    public void setStatus(String status) { this.status = status; }
    public String getSource() { return source; }
    public void setSource(String source) { this.source = source; }
    public Integer getAuthorId() { return authorId; }
    public void setAuthorId(Integer authorId) { this.authorId = authorId; }
    public LocalDateTime getCreatedAt() { return createdAt; }
    public void setCreatedAt(LocalDateTime createdAt) { this.createdAt = createdAt; }
}
