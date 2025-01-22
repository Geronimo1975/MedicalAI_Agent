"""
Telemedicine Platform Project Structure

📦 Root
├── 📂 app/
│   ├── __init__.py          # Flask application initialization
│   ├── models.py            # Database models
│   ├── api.py              # API routes and endpoints
│   ├── auth.py             # Authentication logic
│   └── chatbot.py          # AI chatbot implementation
├── 📂 client/
│   ├── 📂 src/
│   │   ├── 📂 components/
│   │   │   ├── 📂 ui/      # Shadcn UI components
│   │   │   ├── appointment-form.tsx
│   │   │   └── video-call.tsx
│   │   ├── 📂 hooks/
│   │   │   ├── use-appointments.ts
│   │   │   ├── use-mobile.tsx
│   │   │   ├── use-toast.ts
│   │   │   └── use-user.ts
│   │   ├── 📂 lib/         # Utility functions
│   │   ├── 📂 pages/
│   │   │   ├── 📂 dashboard/
│   │   │   │   ├── admin.tsx
│   │   │   │   ├── doctor.tsx
│   │   │   │   └── patient.tsx
│   │   │   ├── auth-page.tsx
│   │   │   └── not-found.tsx
│   │   ├── App.tsx         # Main React application
│   │   ├── index.css       # Global styles
│   │   └── main.tsx        # Application entry point
│   └── index.html
├── 📂 db/                  # Database configuration and migrations
├── 📂 server/
│   ├── routes.ts           # Express server routes
│   ├── auth.ts             # Authentication middleware
│   ├── index.ts            # Server entry point
│   └── vite.ts             # Vite configuration
├── run.py                  # Flask application runner
├── drizzle.config.ts       # Drizzle ORM configuration
├── package.json            # Node.js dependencies
├── tsconfig.json           # TypeScript configuration
├── postcss.config.js       # PostCSS configuration
├── tailwind.config.ts      # Tailwind CSS configuration
├── theme.json             # Application theme configuration
├── vite.config.ts         # Vite bundler configuration
└── requirements.txt       # Python dependencies

Key Features:
1. Multi-role authentication (Patient, Doctor, Admin)
2. Appointment management
3. Video consultations
4. Medical records management
5. AI-powered symptom triage chatbot
   - OpenAI GPT-4 integration
   - Hugging Face BioGPT support
   - Meta's Llama-2 integration
6. Prescription management
7. Document sharing
"""