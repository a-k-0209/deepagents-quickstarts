# Tech Radar: Best Python Frameworks for Data Validation

## 1. Radar Scope
This radar focuses on Python frameworks specifically designed for data validation. It evaluates popular and emerging frameworks based on their maturity, adoption, ecosystem integration, risk factors, and strategic value for Python developers needing robust data validation solutions.

## 2. Radar Criteria
Decisions were made considering the following signals:
- Community adoption and popularity
- Framework maturity and stability
- Feature set and extensibility
- Performance considerations
- Ecosystem integration with popular Python tools and frameworks
- Maintenance activity and support
- Known risks and trade-offs

## 3. Radar Entries

### Adopt

**Pydantic**  
*Category:* Framework  
*Rationale:* Pydantic leverages Python type annotations to provide declarative, powerful data validation and parsing. It is widely adopted, especially in modern Python web frameworks like FastAPI. It offers nested models, detailed error reporting, and strong ecosystem support.  
*Risks / Trade-offs:* Some performance overhead in large-scale validation scenarios; learning curve for advanced features.  
*Confidence Level:* High  
*Re-evaluation Trigger:* Significant changes in adoption, major security vulnerabilities, or emergence of superior alternatives.

### Trial

**Marshmallow**  
*Category:* Framework  
*Rationale:* Marshmallow is a mature, stable schema-based validation and serialization library. It is popular in API development with Flask and Django, supports custom validators, and has strong ecosystem integration.  
*Risks / Trade-offs:* Verbose syntax and some performance overhead compared to newer frameworks.  
*Confidence Level:* High  
*Re-evaluation Trigger:* Decline in community support or emergence of more efficient alternatives.

### Assess

**Cerberus**  
*Category:* Framework  
*Rationale:* Cerberus is a lightweight, schema-based validation library that is easy to extend with custom rules. It has a smaller community and fewer integrations but is suitable for simpler or lightweight projects.  
*Risks / Trade-offs:* Limited ecosystem and potential concerns about long-term maintenance.  
*Confidence Level:* Medium  
*Re-evaluation Trigger:* Growth in adoption or discovery of critical issues.

### Hold

No frameworks currently fall into the Hold quadrant based on current evidence.

---

### Sources
[1] Python Data Validation with Pydantic - Nineleaps Blog: https://www.nineleaps.com/blog/python-data-validation-with-pydantic/
[2] Introduction to Marshmallow in Python - Better Stack Community: https://betterstack.com/community/guides/scaling-python/marshmallow-explained/
[3] Python Data Validation for Beginners with Cerberus - Wellsr.com: https://wellsr.com/python/python-data-validation-with-cerberus/
[4] General ecosystem knowledge and framework documentation
