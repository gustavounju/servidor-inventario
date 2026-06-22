# SkillSpector Security Report

**Skill:** unknown  
**Source:** `G:\unju2025\google gravity\ServidorInventario\.agents\skills`  
**Scanned:** 2026-06-22 02:18:54 UTC  

## Risk Assessment

| Metric | Value |
|--------|-------|
| Score | 100/100 |
| Severity | CRITICAL |
| Recommendation | DO NOT INSTALL |

## Components (40)

| File | Type | Lines | Executable |
|------|------|-------|------------|
| `api-and-interface-design\SKILL.md` | markdown | 294 | No |
| `browser-testing-with-devtools\SKILL.md` | markdown | 304 | No |
| `ci-cd-and-automation\SKILL.md` | markdown | 390 | No |
| `code-review-and-quality\SKILL.md` | markdown | 347 | No |
| `code-simplification\SKILL.md` | markdown | 331 | No |
| `context-engineering\SKILL.md` | markdown | 289 | No |
| `cso\SKILL.md` | markdown | 78 | No |
| `debugging-and-error-recovery\SKILL.md` | markdown | 300 | No |
| `deploy\SKILL.md` | markdown | 79 | No |
| `deprecation-and-migration\SKILL.md` | markdown | 206 | No |
| `document-release\SKILL.md` | markdown | 47 | No |
| `documentation-and-adrs\SKILL.md` | markdown | 278 | No |
| `doubt-driven-development\SKILL.md` | markdown | 243 | No |
| `frontend-design\LICENSE.txt` | text | 177 | No |
| `frontend-design\SKILL.md` | markdown | 67 | No |
| `frontend-ui-engineering\SKILL.md` | markdown | 328 | No |
| `git-workflow-and-versioning\SKILL.md` | markdown | 300 | No |
| `guard\SKILL.md` | markdown | 74 | No |
| `idea-refine\SKILL.md` | markdown | 178 | No |
| `idea-refine\examples.md` | markdown | 238 | No |
| `idea-refine\frameworks.md` | markdown | 99 | No |
| `idea-refine\refinement-criteria.md` | markdown | 113 | No |
| `idea-refine\scripts\idea-refine.sh` | shell | 15 | Yes |
| `incremental-implementation\SKILL.md` | markdown | 245 | No |
| `interview-me\SKILL.md` | markdown | 225 | No |
| `observability-and-instrumentation\SKILL.md` | markdown | 201 | No |
| `office-hours\SKILL.md` | markdown | 84 | No |
| `performance-optimization\SKILL.md` | markdown | 350 | No |
| `plan-ceo-review\SKILL.md` | markdown | 60 | No |
| `plan-eng-review\SKILL.md` | markdown | 66 | No |
| `planning-and-task-breakdown\SKILL.md` | markdown | 223 | No |
| `qa\SKILL.md` | markdown | 51 | No |
| `review\SKILL.md` | markdown | 61 | No |
| `security-and-hardening\SKILL.md` | markdown | 461 | No |
| `ship\SKILL.md` | markdown | 53 | No |
| `shipping-and-launch\SKILL.md` | markdown | 309 | No |
| `source-driven-development\SKILL.md` | markdown | 194 | No |
| `spec-driven-development\SKILL.md` | markdown | 200 | No |
| `test-driven-development\SKILL.md` | markdown | 383 | No |
| `using-agent-skills\SKILL.md` | markdown | 189 | No |

## Issues (23)

### 🟢 LOW: EA3

**Location:** `code-simplification\SKILL.md:103`  
**Confidence:** 75%  

**Message:** Scope Creep

**Remediation:** Limit the skill's scope to its documented purpose. Remove instructions that enable the agent to perform actions outside its stated functionality.

---

### 🟡 MEDIUM: EA1

**Location:** `context-engineering\SKILL.md:74`  
**Confidence:** 85%  

**Message:** Unrestricted Tool Access

**Remediation:** Restrict tool access to only the tools required for the skill's stated purpose. Use an explicit allowlist rather than granting blanket access.

---

### 🟡 MEDIUM: EA2

**Location:** `context-engineering\SKILL.md:66`  
**Confidence:** 75%  

**Message:** Autonomous Decision Making

**Remediation:** Add human-in-the-loop confirmation for destructive, irreversible, or high-impact operations. Never auto-execute commands that modify files, send data, or alter system state.

---

### 🟡 MEDIUM: EA2

**Location:** `context-engineering\SKILL.md:280`  
**Confidence:** 75%  

**Message:** Autonomous Decision Making

**Remediation:** Add human-in-the-loop confirmation for destructive, irreversible, or high-impact operations. Never auto-execute commands that modify files, send data, or alter system state.

---

### 🟢 LOW: EA3

**Location:** `frontend-design\LICENSE.txt:28`  
**Confidence:** 70%  

**Message:** Scope Creep

**Remediation:** Limit the skill's scope to its documented purpose. Remove instructions that enable the agent to perform actions outside its stated functionality.

---

### 🟢 LOW: EA3

**Location:** `frontend-design\LICENSE.txt:33`  
**Confidence:** 70%  

**Message:** Scope Creep

**Remediation:** Limit the skill's scope to its documented purpose. Remove instructions that enable the agent to perform actions outside its stated functionality.

---

### 🟢 LOW: EA3

**Location:** `frontend-design\LICENSE.txt:56`  
**Confidence:** 70%  

**Message:** Scope Creep

**Remediation:** Limit the skill's scope to its documented purpose. Remove instructions that enable the agent to perform actions outside its stated functionality.

---

### 🟢 LOW: EA3

**Location:** `frontend-design\LICENSE.txt:161`  
**Confidence:** 70%  

**Message:** Scope Creep

**Remediation:** Limit the skill's scope to its documented purpose. Remove instructions that enable the agent to perform actions outside its stated functionality.

---

### 🟡 MEDIUM: EA2

**Location:** `planning-and-task-breakdown\SKILL.md:209`  
**Confidence:** 75%  

**Message:** Autonomous Decision Making

**Remediation:** Add human-in-the-loop confirmation for destructive, irreversible, or high-impact operations. Never auto-execute commands that modify files, send data, or alter system state.

---

### 🟡 MEDIUM: EA1

**Location:** `security-and-hardening\SKILL.md:305`  
**Confidence:** 80%  

**Message:** Unrestricted Tool Access

**Remediation:** Restrict tool access to only the tools required for the skill's stated purpose. Use an explicit allowlist rather than granting blanket access.

---

### 🟡 MEDIUM: EA2

**Location:** `spec-driven-development\SKILL.md:80`  
**Confidence:** 75%  

**Message:** Autonomous Decision Making

**Remediation:** Add human-in-the-loop confirmation for destructive, irreversible, or high-impact operations. Never auto-execute commands that modify files, send data, or alter system state.

---

### 🟡 MEDIUM: EA2

**Location:** `using-agent-skills\SKILL.md:117`  
**Confidence:** 75%  

**Message:** Autonomous Decision Making

**Remediation:** Add human-in-the-loop confirmation for destructive, irreversible, or high-impact operations. Never auto-execute commands that modify files, send data, or alter system state.

---

### 🟡 MEDIUM: EA2

**Location:** `using-agent-skills\SKILL.md:132`  
**Confidence:** 85%  

**Message:** Autonomous Decision Making

**Remediation:** Add human-in-the-loop confirmation for destructive, irreversible, or high-impact operations. Never auto-execute commands that modify files, send data, or alter system state.

---

### 🔴 HIGH: PE3

**Location:** `context-engineering\SKILL.md:65`  
**Confidence:** 60%  

**Message:** Credential Access

**Remediation:** Remove references to credential paths. Use environment variables or secrets managers. For docs, use placeholder paths (e.g., /path/to/config). Never load .env or token files in production code paths.

---

### 🔴 HIGH: PE3

**Location:** `security-and-hardening\SKILL.md:334`  
**Confidence:** 60%  

**Message:** Credential Access

**Remediation:** Remove references to credential paths. Use environment variables or secrets managers. For docs, use placeholder paths (e.g., /path/to/config). Never load .env or token files in production code paths.

---

### 🔴 HIGH: PE3

**Location:** `security-and-hardening\SKILL.md:337`  
**Confidence:** 60%  

**Message:** Credential Access

**Remediation:** Remove references to credential paths. Use environment variables or secrets managers. For docs, use placeholder paths (e.g., /path/to/config). Never load .env or token files in production code paths.

---

### 🔴 HIGH: PE3

**Location:** `security-and-hardening\SKILL.md:338`  
**Confidence:** 60%  

**Message:** Credential Access

**Remediation:** Remove references to credential paths. Use environment variables or secrets managers. For docs, use placeholder paths (e.g., /path/to/config). Never load .env or token files in production code paths.

---

### 🔴 HIGH: P1

**Location:** `browser-testing-with-devtools\SKILL.md:65`  
**Confidence:** 80%  

**Message:** Instruction Override

**Remediation:** Remove or rewrite any text that instructs the agent to ignore prompts, override safety rules, or trust unverified content. Ensure skill content cannot be injected to alter agent behavior.

---

### 🔴 HIGH: RA1

**Location:** `code-simplification\SKILL.md:155`  
**Confidence:** 70%  

**Message:** Self-Modification

**Remediation:** Prevent the skill from modifying its own code, SKILL.md, or configuration files. Treat skill files as read-only at runtime.

---

### 🔴 HIGH: TM1

**Location:** `api-and-interface-design\SKILL.md:165`  
**Confidence:** 80%  

**Message:** Tool Parameter Abuse

**Remediation:** Validate all tool parameters against an allowlist. Reject dangerous parameter values (shell=True, --force, -rf /) and use safe defaults.

---

### 🔴 HIGH: TM1

**Location:** `git-workflow-and-versioning\SKILL.md:189`  
**Confidence:** 65%  

**Message:** Tool Parameter Abuse

**Remediation:** Validate all tool parameters against an allowlist. Reject dangerous parameter values (shell=True, --force, -rf /) and use safe defaults.

---

### 🔴 HIGH: TM1

**Location:** `guard\SKILL.md:46`  
**Confidence:** 70%  

**Message:** Tool Parameter Abuse

**Remediation:** Validate all tool parameters against an allowlist. Reject dangerous parameter values (shell=True, --force, -rf /) and use safe defaults.

---

### 🔴 HIGH: TM1

**Location:** `guard\SKILL.md:46`  
**Confidence:** 65%  

**Message:** Tool Parameter Abuse

**Remediation:** Validate all tool parameters against an allowlist. Reject dangerous parameter values (shell=True, --force, -rf /) and use safe defaults.

---

## Metadata

- **Executable Scripts:** Yes

*Generated by SkillSpector v2.2.3*