package com.project.LcPlag.repository;

import com.project.LcPlag.model.Submissions;
import org.springframework.data.jpa.repository.JpaRepository;

public interface SubmissionRepository  extends JpaRepository<Submissions, Long> {
}
