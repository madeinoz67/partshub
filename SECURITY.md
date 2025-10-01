# Security Policy

## Known Security Issues

### ecdsa (CVE-2024-23342, PVE-2024-64396)

**Status**: No fix available (all versions affected)
**Severity**: Medium
**Component**: `ecdsa` (transitive dependency via `python-jose[cryptography]`)

**Issue**: The python-ecdsa library is vulnerable to timing attacks (Minerva attack) and lacks side-channel attack protections due to Python's lack of constant-time primitives.

**Mitigation**:
- This vulnerability requires an attacker to have local access to observe timing information
- JWT tokens are used for authentication, not for cryptographic operations requiring side-channel protection
- We monitor for updates to either `ecdsa` or `python-jose` that might resolve this issue
- Consider migrating to alternative JWT libraries in future if a secure alternative becomes available

**References**:
- https://data.safetycli.com/v/64459/f17
- https://data.safetycli.com/v/64396/f17

## Reporting a Vulnerability

If you discover a security vulnerability, please email the maintainers directly rather than opening a public issue.

## Security Updates

We regularly update dependencies to address security vulnerabilities. Our CI pipeline:
- Runs `safety` to scan Python dependencies
- Runs `bandit` to scan code for security issues
- Runs `npm audit` to scan frontend dependencies
- **Fails the build** if critical vulnerabilities are found

See `.github/workflows/ci.yml` for implementation details.
