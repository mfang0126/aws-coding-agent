# Quick Fixes for Architecture Document

**Date:** 2025-10-29
**Status:** 2 minor corrections + 1 enhancement needed

---

## TL;DR - What Needs to Change

✅ **Good News:** Architecture is 95% correct!
⚠️ **Action Needed:** Fix 2 CLI parameter issues + add callback URL guidance

---

## Fix #1: Remove `region` Parameter from Delete Call

### Location
`src/auth/setup_provider.py` - Line ~174

### Current (Incorrect)
```python
client.delete_oauth2_credential_provider(
    name='github-provider',
    region=settings.aws_region  # ❌ REMOVE THIS
)
```

### Fixed
```python
# Region already set during client creation
client = boto3.client('bedrock-agentcore-control', region_name=settings.aws_region)

# No region parameter needed in method call
client.delete_oauth2_credential_provider(name='github-provider')
```

### Why This Matters
The `delete_oauth2_credential_provider()` method does not accept a `region` parameter. Region is specified once during client initialization, not in individual API calls.

---

## Fix #2: Remove `region_name` Parameter from List Call

### Location
`src/auth/setup_provider.py` - Line ~202

### Current (Incorrect)
```python
providers = client.list_oauth2_credential_providers(
    region_name=settings.aws_region  # ❌ REMOVE THIS
)
```

### Fixed
```python
# Region already set during client creation
client = boto3.client('bedrock-agentcore-control', region_name=settings.aws_region)

# No region_name parameter needed
providers = client.list_oauth2_credential_providers()
```

### Why This Matters
Same as Fix #1 - region is set once during client creation, not passed to individual methods.

---

## Enhancement #1: Add Callback URL Guidance

### Location
`src/auth/setup_provider.py` - After provider creation (Line ~193)

### Add This Code
```python
response = client.create_oauth2_credential_provider(...)

# Extract important information
provider_arn = response['credentialProviderArn']
callback_url = response.get('callbackUrl')
secret_arn = response['clientSecretArn']['secretArn']

print(f"✅ Created OAuth provider: {provider_arn}")
print(f"   Provider name: github-provider")
print(f"   Vendor: GithubOauth2")
print()
print("=" * 70)
print("🔐 IMPORTANT: GitHub OAuth App Configuration Required")
print("=" * 70)
print()
print("You MUST add this callback URL to your GitHub OAuth App:")
print(f"  {callback_url}")
print()
print("Steps:")
print("  1. Go to https://github.com/settings/developers")
print("  2. Select your OAuth App")
print("  3. Add the callback URL above to 'Authorization callback URL'")
print("  4. Save changes")
print()
print(f"📋 Client secret stored in Secrets Manager:")
print(f"   ARN: {secret_arn}")
print("=" * 70)
```

### Why This Matters
**Critical:** Without registering the callback URL in GitHub, OAuth authentication will fail. This guidance prevents a common setup mistake.

---

## Complete Corrected Function

```python
def create_github_oauth_provider() -> str:
    """
    Create OAuth2 credential provider for GitHub in AgentCore Identity.
    Corrected version based on AWS documentation review.
    """
    # ✅ CORRECT: Region specified during client creation
    client = boto3.client('bedrock-agentcore-control', region_name=settings.aws_region)

    # Delete existing provider if it exists
    try:
        print("🔍 Checking for existing provider...")

        # ✅ CORRECT: No region_name parameter
        providers = client.list_oauth2_credential_providers()

        if any(p['name'] == 'github-provider' for p in providers.get('credentialProviders', [])):
            print("♻️  Deleting existing provider...")

            # ✅ CORRECT: No region parameter
            client.delete_oauth2_credential_provider(name='github-provider')

            import time
            time.sleep(5)  # Wait for cleanup
    except Exception as e:
        print(f"ℹ️  No existing provider to delete: {e}")

    # Create new provider
    # ✅ CORRECT: camelCase parameter names match API
    response = client.create_oauth2_credential_provider(
        name='github-provider',
        credentialProviderVendor='GithubOauth2',
        oauth2ProviderConfigInput={
            'githubOauth2ProviderConfig': {
                'clientId': settings.github_client_id.get_secret_value(),
                'clientSecret': settings.github_client_secret.get_secret_value()
            }
        }
    )

    # Extract and display results
    provider_arn = response['credentialProviderArn']
    callback_url = response.get('callbackUrl')
    secret_arn = response['clientSecretArn']['secretArn']

    print(f"✅ Created OAuth provider: {provider_arn}")
    print(f"   Provider name: github-provider")
    print(f"   Vendor: GithubOauth2")
    print()
    print("=" * 70)
    print("🔐 IMPORTANT: GitHub OAuth App Configuration Required")
    print("=" * 70)
    print()
    print("You MUST add this callback URL to your GitHub OAuth App:")
    print(f"  {callback_url}")
    print()
    print("Steps:")
    print("  1. Go to https://github.com/settings/developers")
    print("  2. Select your OAuth App")
    print("  3. Add the callback URL above to 'Authorization callback URL'")
    print("  4. Save changes")
    print()
    print(f"📋 Client secret stored in Secrets Manager:")
    print(f"   ARN: {secret_arn}")
    print("=" * 70)

    return provider_arn
```

---

## Testing Checklist

After applying fixes:

- [ ] Remove `region` parameter from `delete_oauth2_credential_provider()` call
- [ ] Remove `region_name` parameter from `list_oauth2_credential_providers()` call
- [ ] Add callback URL display and guidance
- [ ] Test provider creation: `python src/auth/setup_provider.py`
- [ ] Verify callback URL appears in output
- [ ] Add callback URL to GitHub OAuth App settings
- [ ] Verify provider creation: Check AWS console or run `verify_provider_setup()`

---

## Reference Implementation

See `/Users/freedom/ai/aws-coding-agent/claudedocs/corrected-oauth-setup.py` for a complete, tested implementation with:
- ✅ All fixes applied
- ✅ Callback URL guidance
- ✅ CLI interface (`create`, `verify`, `list`, `delete` commands)
- ✅ Comprehensive error handling
- ✅ Detailed output formatting

---

## AWS Documentation Sources

1. **OAuth2 Provider Setup:**
   https://docs.aws.amazon.com/bedrock-agentcore/latest/devguide/identity-getting-started-google.html

2. **CreateOauth2CredentialProvider API:**
   https://docs.aws.amazon.com/bedrock-agentcore-control/latest/APIReference/API_CreateOauth2CredentialProvider.html

3. **GitHub Provider Config:**
   https://docs.aws.amazon.com/bedrock-agentcore-control/latest/APIReference/API_GithubOauth2ProviderConfigInput.html

---

## What's Already Correct (No Changes Needed)

✅ OAuth2 provider creation command structure
✅ GitHub provider vendor name (`GithubOauth2`)
✅ Provider configuration structure (`githubOauth2ProviderConfig`)
✅ `@requires_access_token` decorator usage
✅ Authentication flow (`USER_FEDERATION` for 3-Legged OAuth)
✅ OAuth URL callback pattern
✅ Deployment sequence
✅ No Gateway needed for this use case

---

## Summary

**Time to Fix:** ~10 minutes
**Complexity:** Low (parameter removal + text output)
**Risk:** None (fixes incorrect API calls that would fail anyway)
**Impact:** Improves setup reliability and prevents common OAuth configuration mistake
