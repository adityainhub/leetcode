package com.project.LcPlag.service;

import com.project.LcPlag.model.Submissions;
import com.project.LcPlag.repository.SubmissionRepository;
import org.springframework.stereotype.Service;

import java.util.List;

@Service
public class SubmissionService {

    private final SubmissionRepository submissionRepository;

    public SubmissionService(SubmissionRepository submissionRepository) {
        this.submissionRepository = submissionRepository;
    }

    public List<Submissions> getAllSubmissions() {
        return submissionRepository.findAll();
    }

    public void saveSubmission(Submissions submission) {
        submissionRepository.save(submission);
    }
}
