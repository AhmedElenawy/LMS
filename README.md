# LMS Backend API (Leado)

**Version:** 2.1.0  
**Framework:** Django / Django REST Framework (DRF)

This is the code-verified backend API for the LMS platform. It handles user authentication, course management, student enrollment, interactive assignments, and payment processing.

## 🚀 Core Features

* **Authentication & Authorization:** * SimpleJWT-based access and refresh tokens.
  * Role-based access control (Students vs. Instructors).
  * OTP flow for account activation and password resets.
  * Google OAuth integration.
* **Course Catalog & Learning:**
  * Public course discovery with search, category, and price filtering.
  * Module and content progression (Text, Video, Image, File, Assignments).
  * Student progress tracking.
* **Interactive Assignments & Exams:**
  * Real-time session management via Redis cache.
  * Autosave functionality for text, file, and MCQ answers.
  * Automated grading for MCQs and instructor-grading for files/essays.
* **Commerce & Payments:**
  * Cart management and coupon code application.
  * Order generation and tracking.
  * Stripe Checkout integration for payment processing.
* **Instructor Management (`/management/*`):**
  * Full CRUD for courses, modules, and content.
  * Discount management.
  * Student enrollment tracking and manual overrides.

## 🛠 Tech Stack

* **Core:** Python, Django, Django REST Framework
* **Auth:** SimpleJWT
* **Cache/Sessions:** Redis (used for exam sessions and OTPs)
* **Payments:** Stripe API
* **Database:** PostgreSQL / SQLite (depending on environment)