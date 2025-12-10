# Technical Scoping Document: Afya Yangu Self-Service Profile Update

## 1. Background & Context

The Afya Yangu application serves as the public-facing portal for Kenya's Universal Health Coverage (UHC) system. During mass registration campaigns (via assisted registration), a streamlined onboarding process was implemented that captured only National ID numbers, creating user records with system-generated Client Registry (CR) numbers but lacking critical biodata elements (phone numbers, self-service PINs). This technical scope addresses the secure enablement of self-service profile completion for these minimally-registered users.

## 2. Technical Architecture

### 2.1 System Components

**Frontend Layer (Afya Yangu Mobile/Web App)**
- React Native/Progressive Web App
- State management for multi-step form flow
- OTP validation UI components
- Secure PIN entry interface with masking

**API Gateway Layer**
- OAuth 2.0 token validation
- Rate limiting (10 requests/minute per National ID)
- Request logging and audit trail generation
- TLS 1.3 encryption for data in transit

**Backend Services Layer**
- Profile Update Service (Node.js/Python microservice)
- OTP Generation & Validation Service (Redis-backed, 5-minute TTL)
- Client Registry Integration Service (FHIR R4 Patient resource updates)
- Audit Logging Service (compliance with Data Protection Act 2019)

**Data Layer**
- PostgreSQL/MariaDB for transactional data
- Redis cache for OTP sessions
- Elasticsearch for audit logs

### 2.2 Architecture Diagram

```mermaid
graph TB
    subgraph Frontend["Afya Yangu Frontend"]
        A[Update Profile Screen]
        B[OTP Validation Screen]
        C[PIN Setup Screen]
        A --> B --> C
    end
    
    subgraph Gateway["API Gateway Layer"]
        D[Rate Limiting]
        E[Authentication]
        F[Request Logging]
        G[Validation]
    end
    
    subgraph Backend["Backend Services"]
        H[Profile Update API]
        I[OTP Service]
        J[Audit Logging Service]
    end
    
    subgraph Data["Data Layer"]
        K[Client Registry OpenCR]
        L[Redis Cache]
        M[PostgreSQL]
    end
    
    Frontend -->|HTTPS/TLS 1.3| Gateway
    Gateway --> Backend
    H --> K
    I --> L
    H --> M
    J --> M
    
    style Frontend fill:#e1f5ff
    style Gateway fill:#fff4e1
    style Backend fill:#e8f5e9
    style Data fill:#f3e5f5
```

## 3. Implementation Flow

### 3.1 User Journey Flow Diagram

```mermaid
flowchart TD
    Start([User clicks Update Profile]) --> Input[Enter National ID + Phone Number]
    Input --> Validate{Backend validates<br/>ID exists in CR}
    Validate -->|ID Not Found| Error1[Error: Invalid ID]
    Validate -->|ID Found| SendOTP[Generate & send OTP to phone]
    SendOTP --> EnterOTP[User enters OTP code]
    EnterOTP --> ValidateOTP{Validate OTP}
    ValidateOTP -->|Invalid| Retry{Retry count<br/>< 3?}
    Retry -->|Yes| EnterOTP
    Retry -->|No| Error2[Error: Max attempts exceeded]
    ValidateOTP -->|Valid| CreatePIN[Prompt user to create PIN]
    CreatePIN --> EnterPIN[Enter PIN + Confirm PIN]
    EnterPIN --> ValidatePIN[Validate PIN rules]
    ValidatePIN --> UpdateCR[Update CR record with<br/>phone + PIN hash]
    UpdateCR --> Success[Show success confirmation]
    Success --> End([End])
    
    style Start fill:#4caf50
    style End fill:#4caf50
    style Error1 fill:#f44336
    style Error2 fill:#f44336
    style Success fill:#8bc34a
```

## 4. Security & Compliance Measures

**Authentication & Authorization**
- National ID validation against Client Registry (CR FHIR endpoint)
- Multi-factor authentication via OTP (SMS gateway integration with Safaricom API)
- PIN hashing using bcrypt (cost factor 12) before storage

**Data Protection (DPA 2019 Compliance)**
- End-to-end encryption for sensitive data fields
- Audit logs capturing all profile update attempts (success/failure)
- Session timeout after 10 minutes of inactivity
- OTP expiry after 5 minutes, maximum 3 validation attempts

**Rate Limiting & Abuse Prevention**
- 10 profile update attempts per National ID per day
- CAPTCHA implementation after 2 failed OTP validations
- Temporary account lock after 5 consecutive failed attempts (24-hour cooldown)

## 5. API Specifications

### 5.1 Profile Update Initiation
```
POST /api/v1/profile/initiate-update
Request: { "nationalId": "12345678", "phoneNumber": "+254712345678" }
Response: { "sessionId": "uuid", "otpSent": true, "expiresIn": 300 }
```

### 5.2 OTP Validation & PIN Setup
```
POST /api/v1/profile/validate-and-update
Request: { 
  "sessionId": "uuid", 
  "otp": "123456",
  "pin": "hashed_pin",
  "phoneNumber": "+254712345678"
}
Response: { "success": true, "crNumber": "CR-00012345" }
```

---

**Author:** Ager Wasongah - Business Solutions Architect 
