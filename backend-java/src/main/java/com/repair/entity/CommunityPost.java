package com.repair.entity;

import javax.persistence.*;
import java.time.LocalDateTime;

@Entity
@Table(name = "community_posts")
public class CommunityPost {
    @Id
    @GeneratedValue(strategy = GenerationType.IDENTITY)
    private Integer id;

    @Column(nullable = false)
    private String title;

    @Column(name = "device_type")
    private String deviceType = "";

    @Column(name = "fault_type")
    private String faultType = "";

    @Column(columnDefinition = "text")
    private String content = "";

    @Column(columnDefinition = "text")
    private String images = "[]";

    @Column(name = "author_id")
    private Integer authorId;

    @Column(name = "author_name")
    private String authorName = "匿名用户";

    private String status = "pending";

    @Column(name = "matched_chapter")
    private String matchedChapter = "";

    private Integer likes = 0;

    @Column(name = "liked_users", columnDefinition = "text")
    private String likedUsers = "[]";

    private Integer views = 0;

    @Column(name = "created_at")
    private LocalDateTime createdAt = LocalDateTime.now();

    @Column(name = "reviewed_at")
    private LocalDateTime reviewedAt;

    @Column(name = "reviewer_id")
    private Integer reviewerId;

    @Column(name = "review_comment")
    private String reviewComment = "";

    public CommunityPost() {}

    public Integer getId() { return id; }
    public void setId(Integer id) { this.id = id; }
    public String getTitle() { return title; }
    public void setTitle(String title) { this.title = title; }
    public String getDeviceType() { return deviceType; }
    public void setDeviceType(String deviceType) { this.deviceType = deviceType; }
    public String getFaultType() { return faultType; }
    public void setFaultType(String faultType) { this.faultType = faultType; }
    public String getContent() { return content; }
    public void setContent(String content) { this.content = content; }
    public String getImages() { return images; }
    public void setImages(String images) { this.images = images; }
    public Integer getAuthorId() { return authorId; }
    public void setAuthorId(Integer authorId) { this.authorId = authorId; }
    public String getAuthorName() { return authorName; }
    public void setAuthorName(String authorName) { this.authorName = authorName; }
    public String getStatus() { return status; }
    public void setStatus(String status) { this.status = status; }
    public String getMatchedChapter() { return matchedChapter; }
    public void setMatchedChapter(String matchedChapter) { this.matchedChapter = matchedChapter; }
    public Integer getLikes() { return likes; }
    public void setLikes(Integer likes) { this.likes = likes; }
    public String getLikedUsers() { return likedUsers; }
    public void setLikedUsers(String likedUsers) { this.likedUsers = likedUsers; }
    public Integer getViews() { return views; }
    public void setViews(Integer views) { this.views = views; }
    public LocalDateTime getCreatedAt() { return createdAt; }
    public void setCreatedAt(LocalDateTime createdAt) { this.createdAt = createdAt; }
    public LocalDateTime getReviewedAt() { return reviewedAt; }
    public void setReviewedAt(LocalDateTime reviewedAt) { this.reviewedAt = reviewedAt; }
    public Integer getReviewerId() { return reviewerId; }
    public void setReviewerId(Integer reviewerId) { this.reviewerId = reviewerId; }
    public String getReviewComment() { return reviewComment; }
    public void setReviewComment(String reviewComment) { this.reviewComment = reviewComment; }
}
