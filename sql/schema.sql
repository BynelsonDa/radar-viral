CREATE DATABASE IF NOT EXISTS radar_viral CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;
USE radar_viral;
CREATE TABLE IF NOT EXISTS videos (video_id VARCHAR(20) PRIMARY KEY,title VARCHAR(500) NOT NULL,channel_title VARCHAR(255),published_at DATETIME,duration_seconds INT NOT NULL,view_count BIGINT NOT NULL DEFAULT 0,like_count BIGINT NULL,comment_count BIGINT NULL,last_seen_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP);
CREATE TABLE IF NOT EXISTS snapshots (id BIGINT AUTO_INCREMENT PRIMARY KEY,video_id VARCHAR(20) NOT NULL,collected_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,view_count BIGINT NOT NULL,like_count BIGINT NULL,comment_count BIGINT NULL,FOREIGN KEY (video_id) REFERENCES videos(video_id),INDEX idx_video_time(video_id,collected_at));
CREATE TABLE IF NOT EXISTS collection_status (job VARCHAR(30) PRIMARY KEY,last_started_at DATETIME NULL,last_success_at DATETIME NULL,last_error VARCHAR(255) NULL,interval_seconds INT NOT NULL);
