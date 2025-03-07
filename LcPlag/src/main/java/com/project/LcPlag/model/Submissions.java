package com.project.LcPlag.model;

import jakarta.persistence.Entity;
import jakarta.persistence.Id;
import jakarta.persistence.Table;

@Entity
@Table(name = "submissions")
public class Submissions {

    @Id
    private Long subm_id;

    private int contest_id;
    private int question_id;
    private int rank;
    private String username;
    private String filename;
    private String language;

    public Submissions() {}

    public Submissions(Long subm_id, int contest_id, int question_id, int rank, String username, String filename, String language) {
        this.subm_id = subm_id;
        this.contest_id = contest_id;
        this.question_id = question_id;
        this.rank = rank;
        this.username = username;
        this.filename = filename;
        this.language = language;
    }

    // Getters and Setters

    public Long getSubm_id() { return subm_id; }
    public void setSubm_id(Long subm_id) { this.subm_id = subm_id; }

    public int getContest_id() { return contest_id; }
    public void setContest_id(int contest_id) { this.contest_id = contest_id; }

    public int getQuestion_id() { return question_id; }
    public void setQuestion_id(int question_id) { this.question_id = question_id; }

    public int getRank() { return rank; }
    public void setRank(int rank) { this.rank = rank; }

    public String getUsername() { return username; }
    public void setUsername(String username) { this.username = username; }

    public String getFilename() { return filename; }
    public void setFilename(String filename) { this.filename = filename; }

    public String getLanguage() { return language; }
    public void setLanguage(String language) { this.language = language; }
}
