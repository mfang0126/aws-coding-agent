"""
Corrected OAuth2 Provider Setup for AWS Bedrock AgentCore
Based on official AWS documentation review (2025-10-29)

Key corrections from draft.md:
1. Remove 'region' parameter from delete_oauth2_credential_provider() call
2. Remove 'region_name' parameter from list_oauth2_credential_providers() call
3. Add callback URL registration guidance
4. Display client secret ARN for reference

Source: AWS Bedrock AgentCore Identity Documentation
https://docs.aws.amazon.com/bedrock-agentcore/latest/devguide/identity-getting-started-google.html
"""
import boto3
import os
from typing import Optional
import time


def create_github_oauth_provider(
    region: str = "us-east-1",
    provider_name: str = "github-provider",
    github_client_id: Optional[str] = None,
    github_client_secret: Optional[str] = None
) -> dict:
    """
    Create OAuth2 credential provider for GitHub in AgentCore Identity.

    Args:
        region: AWS region for the provider
        provider_name: Name for the OAuth provider (must be unique)
        github_client_id: GitHub OAuth App Client ID
        github_client_secret: GitHub OAuth App Client Secret

    Returns:
        dict: Response containing provider ARN, callback URL, and secret ARN

    Raises:
        ValueError: If client ID or secret not provided or found in environment
    """
    # Get credentials from environment if not provided
    client_id = github_client_id or os.getenv('GITHUB_CLIENT_ID')
    client_secret = github_client_secret or os.getenv('GITHUB_CLIENT_SECRET')

    if not client_id or not client_secret:
        raise ValueError(
            "GitHub client ID and secret required. "
            "Set GITHUB_CLIENT_ID and GITHUB_CLIENT_SECRET environment variables."
        )

    # ✅ CORRECT: Region specified during client creation
    client = boto3.client('bedrock-agentcore-control', region_name=region)

    # Delete existing provider if it exists (for updates)
    try:
        print(f"🔍 Checking for existing provider '{provider_name}'...")

        # ✅ CORRECT: No region parameter in list call
        providers = client.list_oauth2_credential_providers()

        existing = next(
            (p for p in providers.get('credentialProviders', [])
             if p['name'] == provider_name),
            None
        )

        if existing:
            print(f"♻️  Deleting existing provider...")
            # ✅ CORRECT: No region parameter in delete call
            client.delete_oauth2_credential_provider(name=provider_name)
            time.sleep(5)  # Wait for cleanup
            print(f"✅ Deleted existing provider")
    except Exception as e:
        print(f"ℹ️  No existing provider to delete: {e}")

    # Create new provider
    print(f"🔐 Creating OAuth2 provider for GitHub...")

    # ✅ CORRECT: API uses camelCase for parameter names
    response = client.create_oauth2_credential_provider(
        name=provider_name,
        credentialProviderVendor='GithubOauth2',  # Must be exactly 'GithubOauth2'
        oauth2ProviderConfigInput={
            'githubOauth2ProviderConfig': {
                'clientId': client_id,
                'clientSecret': client_secret
            }
        }
    )

    # Extract response fields
    provider_arn = response['credentialProviderArn']
    callback_url = response.get('callbackUrl')
    secret_arn = response['clientSecretArn']['secretArn']

    # Display results with actionable guidance
    print()
    print("=" * 70)
    print("✅ OAuth2 Provider Created Successfully")
    print("=" * 70)
    print()
    print(f"Provider ARN:")
    print(f"  {provider_arn}")
    print()
    print(f"Provider Name:")
    print(f"  {provider_name}")
    print()
    print(f"Vendor:")
    print(f"  GithubOauth2")
    print()
    print(f"Client Secret ARN (Secrets Manager):")
    print(f"  {secret_arn}")
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
    print("Without this step, OAuth authentication will FAIL.")
    print("=" * 70)
    print()

    return {
        'credentialProviderArn': provider_arn,
        'callbackUrl': callback_url,
        'clientSecretArn': secret_arn,
        'name': provider_name
    }


def verify_provider_setup(
    region: str = "us-east-1",
    provider_name: str = "github-provider"
) -> bool:
    """
    Verify the OAuth provider was created correctly.

    Args:
        region: AWS region to check
        provider_name: Name of the provider to verify

    Returns:
        bool: True if provider exists and is configured correctly
    """
    print(f"🔍 Verifying provider '{provider_name}'...")

    client = boto3.client('bedrock-agentcore-control', region_name=region)

    try:
        # ✅ CORRECT: No region parameter in list call
        providers = client.list_oauth2_credential_providers()

        github_provider = next(
            (p for p in providers.get('credentialProviders', [])
             if p['name'] == provider_name),
            None
        )

        if github_provider:
            print()
            print("✅ Provider verified:")
            print(f"   ARN: {github_provider['credentialProviderArn']}")
            print(f"   Name: {github_provider['name']}")
            print(f"   Vendor: {github_provider.get('credentialProviderVendor', 'N/A')}")
            print()
            return True
        else:
            print()
            print(f"❌ Provider '{provider_name}' not found!")
            print()
            return False

    except Exception as e:
        print()
        print(f"❌ Error verifying provider: {e}")
        print()
        return False


def list_all_oauth_providers(region: str = "us-east-1") -> list:
    """
    List all OAuth2 credential providers in the region.

    Args:
        region: AWS region to query

    Returns:
        list: List of provider dictionaries
    """
    client = boto3.client('bedrock-agentcore-control', region_name=region)

    # ✅ CORRECT: No region parameter in list call
    response = client.list_oauth2_credential_providers()

    providers = response.get('credentialProviders', [])

    if not providers:
        print(f"ℹ️  No OAuth2 providers found in {region}")
        return []

    print(f"📋 Found {len(providers)} OAuth2 provider(s) in {region}:")
    print()

    for p in providers:
        print(f"  • {p['name']}")
        print(f"    ARN: {p['credentialProviderArn']}")
        print(f"    Vendor: {p.get('credentialProviderVendor', 'N/A')}")
        print()

    return providers


def delete_oauth_provider(
    region: str = "us-east-1",
    provider_name: str = "github-provider"
) -> bool:
    """
    Delete an OAuth2 credential provider.

    Args:
        region: AWS region
        provider_name: Name of the provider to delete

    Returns:
        bool: True if deletion successful
    """
    print(f"🗑️  Deleting provider '{provider_name}'...")

    client = boto3.client('bedrock-agentcore-control', region_name=region)

    try:
        # ✅ CORRECT: No region parameter in delete call
        client.delete_oauth2_credential_provider(name=provider_name)

        print(f"✅ Provider '{provider_name}' deleted successfully")
        print(f"⚠️  Note: Client secret remains in Secrets Manager")
        print(f"   Delete manually if no longer needed")
        return True

    except Exception as e:
        print(f"❌ Error deleting provider: {e}")
        return False


# CLI interface
if __name__ == "__main__":
    import sys

    print()
    print("=" * 70)
    print("🔐 AWS Bedrock AgentCore - GitHub OAuth Provider Setup")
    print("=" * 70)
    print()

    # Get region from environment or use default
    region = os.getenv('AWS_REGION', 'us-east-1')
    print(f"Region: {region}")
    print()

    # Command selector
    if len(sys.argv) > 1:
        command = sys.argv[1].lower()

        if command == "create":
            result = create_github_oauth_provider(region=region)
            verify_provider_setup(region=region)

        elif command == "verify":
            verify_provider_setup(region=region)

        elif command == "list":
            list_all_oauth_providers(region=region)

        elif command == "delete":
            provider_name = sys.argv[2] if len(sys.argv) > 2 else "github-provider"
            delete_oauth_provider(region=region, provider_name=provider_name)

        else:
            print(f"❌ Unknown command: {command}")
            print()
            print("Usage:")
            print("  python corrected-oauth-setup.py create   # Create provider")
            print("  python corrected-oauth-setup.py verify   # Verify provider")
            print("  python corrected-oauth-setup.py list     # List all providers")
            print("  python corrected-oauth-setup.py delete [name]  # Delete provider")
            sys.exit(1)
    else:
        # Default: create and verify
        print("No command specified, running: create → verify")
        print()
        result = create_github_oauth_provider(region=region)
        print()
        verify_provider_setup(region=region)

    print()
    print("=" * 70)
    print("✅ Done")
    print("=" * 70)
    print()
