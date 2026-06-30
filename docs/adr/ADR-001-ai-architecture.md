# ADR-001: AI 架构总体方案

## 状态

已批准（2026-06-27）

## 背景

参加第十五届中国软件杯 A1 赛题"基于多模态大模型技术的设备检修知识检索与作业系统"。需要设计 AI/算法层的完整技术方案，适配 LoongArch + 银河麒麟 + 8GB 内存的部署环境。

## 决策

### 架构

- Python 保留为 AI 微服务（独立部署），Java 后端通过 gRPC 调用
- 龙芯上只跑 PostgreSQL + Apache AGE + pgvector
- AI 推理（LLM / YOLO / 语音）走云端 API 或开发机

### 知识图谱

- **PostgreSQL + Apache AGE**（图数据库，Cypher 查询）
- 冷启动来源：手册 JSON → 自动生成 Cypher 脚本 → 写入 AGE
- 案例上传：NLP 提取实体 + 匹配图谱节点 + 自动挂载

### 向量检索

- **BGE-base-zh-v1.5**（文本向量化，CPU，~400MB）
- **pgvector**（向量存储与检索，1024维）
- 图片理解用 Qwen2.5-VL API，不做独立图向量

### 视频分析

- 条件触发 + 异步 Workers（非固定抽帧）
- YOLOv8n ONNX 做零件检测（CPU，6MB）
- Qwen2.5-VL API 做画面理解
- 竞赛演示用预录视频代替实时摄像头

### 语音

- Sherpa-ONNX（语音转文字，C++，跨平台）
- Edge-TTS（文字转语音，云端免费 API）

### 大模型

- 云端：DeepSeek / Qwen API（对话兜底 + 方案生成）
- 混合模式：默认走云端，hybrid 下保留本地备选

### 数据存储（对话 + 案例 + 日志）

- 全部使用 PostgreSQL 同一数据库
- 不引入 Redis / MongoDB 等额外存储

## 理由

- 统一技术栈降低运维复杂度，一个 PG 跑全部
- 8GB LoongArch 跑不动 PyTorch、3B 本地模型、多个 ONNX 同时推理
- AGE + pgvector 在同一数据库内，避免跨存储的 JOIN 难题
- 演示时用预录视频可保证 100% 成功率

## 代价

- Python AI 微服务与 Java 后端之间引入 gRPC 调用延迟
- Qwen2.5-VL API 需要网络，离线模式下图片理解降级为文字描述
- 竞赛文档需要说明"AI 层通过局域网调用开发机/云端"
