App Overview
EduLine is an educational AI-adaptive learning tutor tailored for WAEC exam preparation. It helps students learn more effectively by providing personalized adaptive practice, performance prediction, and focus-enhancement tools. The initial version requires a consistent internet connection. The app includes subject-specific MCQs and study insights to improve student pass rates.

(video link placeholder)

Case Study: WAEC Performance in Kwara State
(Content remains unchanged as it provides context for the problem, even if the immediate solution differs.)

Problem Statement
Between 2016 and 2024, 54% of WAEC candidates in Kwara State passed five subjects, including Mathematics and English. In 2020, during the COVID-19 pandemic, only 7,548 out of 21,154 candidates were successful. The year 2024 has been identified as showing a ‘noticeable decline’ in performance. Students in rural and low-income areas struggle with poor internet connectivity and high data costs, limiting their access to modern learning tools, while their peers in urban centers face overcrowded classrooms, noise, and distractions that reduce learning effectiveness. Existing AI tutoring platforms are not fully effective in this context because they often rely heavily on consistent internet access.

Proposed Solution
Eduline bridges these gaps by delivering an adaptive AI learning platform with:

WAEC-specific MCQs and past-paper-style questions.

Predictive student performance analysis.

Personalized adaptive learning paths.
Note: A fully offline mode is a critical part of our long-term vision to address connectivity issues and is planned for a future release.

Key Features and Functional Requirements (Current Scope - Online Only)
Core Features

Personalized Learning Dashboard

Requires an internet connection to load.

Shows student progress, weak areas, and predicted performance.

Includes charts/graphs of improvement trends.

Online Question Bank & Clustering

2,000+ WAEC-style MCQs (English and Mathematics) stored and served from the cloud.

AI-powered clustering organizes questions by subject/topic/difficulty on the server.

Performance Prediction & Adaptation

Classifier models predict performance (cloud-based processing).

Adaptive logic suggests the next learning path in real-time.

Teacher/Guardian Module

Web-based portal for teachers/guardians to track student progress over time.

Provides targeted recommendations for improvement.

User Experience (UX) Design

Accessibility: Simple navigation and large buttons.

Customization: Choose subjects, difficulty levels, and notification style.

Feedback loop: Students can report confusing questions or suggest improvements (requires internet connection).

User Interface (UI) Design

Framework: Streamlit / Streamlit Cloud

User Flow (Online)

Onboarding: Register with phone/email (internet required). Quick setup of subjects and study goals.

Daily Use: Start practice quiz → get instant feedback. Check personalized dashboard → adaptive path updated.

Weekly Activities: Review insights and predicted WAEC score. Adjust study plan accordingly.

Emergency/Support Use: In-app help center (online FAQs). Feedback submission (requires online connection).

(User Personas, User Story, and Journey Map remain valid as they describe user needs and emotions, not technical implementation.)

Technology Stack (Current - Online First)
Backend: Node.js / Python (Cloud API)

Frontend: Streamlit/Streamlit Cloud (cross-platform)

AI Models: Scikit-learn / TensorFlow (Cloud-based inference)

Database: Cloud-based SQL (e.g., PostgreSQL)

Future Roadmap & Developments
The following features are critical to our mission but are designated for future development phases to ensure a timely launch of our core online product.

Phase 2: Offline & Expansion

Offline Mode: Full application functionality available without an internet connection after initial setup and sync. Data will sync automatically when a connection is re-established.

Local Database: Implementation of SQLite or a lightweight local DB for offline data storage.

Offline AI Models: Integration of TensorFlow Lite or ONNX models for on-device clustering & classification.

Data Encryption: AES-256 encryption for student data stored on-device.

Phase 3: Enhanced Engagement & Access

Peer/community engagement (study forums).

Multilingual support (English + local languages).

Progress certificates for motivation.

Gamification (badges, study streaks).

Phase 4: Advanced Features

AI chatbot tutor (offline-capable).

Expand to all WAEC subjects.

Teacher dashboards with predictive insights.

Integration with WAEC-style past paper updates.

National rollout, government/NGO partnerships.

AR learning (science experiments, 3D diagrams).

Physics, Chemistry practical Video links (downloadable for offline access).

Compliance
Compliance with local data privacy laws (Nigeria Data Protection Act) for online data handling.

Future: Encryption and privacy protocols for on-device data in the offline release.

KPIs
Student retention rate.

WAEC practice completion rate.

Predicted vs actual WAEC performance accuracy.

Teacher adoption rate.

Functional Requirements (Current)
Online quizzes + cloud-based adaptive logic.

Cloud-based performance prediction per subject.

Teacher/guardian web portal.

Exportable reports (PDF/CSV).

Non-Functional Requirements
Performance: Quizzes and dashboards load quickly over a standard internet connection.

Security: Secure transmission (HTTPS/TLS) and storage for all user data.

Scalability: Cloud infrastructure supports 1M+ users.

Reliability: 99.9% uptime for all cloud services.

Usability: Easy for low-tech users.

Compatibility: PC and Android-first, iOS next.

Conclusion
EduLine Version 1 provides an AI-powered, online learning experience to help WAEC students track their progress and improve their chances of success. We are committed to addressing the digital divide through our planned Offline Mode in a subsequent release, which will ensure equitable access for students in low-connectivity areas.